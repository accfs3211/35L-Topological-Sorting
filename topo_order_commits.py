import os
import zlib
import hashlib
import sys
class commitNode:
        def __init__(self, commitHash):
            self.commitHash = commitHash
            self.parents = list()
            self.children = list()
            self.heads = list()
            self.mergeStartingPoint = 0
def getPath():
    currentPath = os.path.abspath(os.curdir)

    while True:
        gitFolder = os.path.join(currentPath, '.git')
        if os.path.exists(gitFolder) and os.path.isdir(gitFolder):
            #print(os.path.join(currentPath, ".git", "objects"))
            break
        parentPath = os.path.dirname(currentPath)

        if currentPath == parentPath:
            print("Not inside a Git repository", file=sys.stderr)
            exit(1)
            break
        
        currentPath = parentPath

    return currentPath


# takes heads, then get all the commit nodes, and fill out the parents, children, and heads for each corresponding commit
def getCommitNodes(heads):
    currentPath = getPath()
    commitNodes = {}
    objectsFolder = os.path.join(currentPath, ".git", "objects")
    # create all the commit nodes and add the parents
    for root, dirs, files in os.walk(objectsFolder):
        for file in files:
            filePath = os.path.join(root, file)

            # reading every single git object 
            with open(filePath, 'rb') as f:
                #if the git object starts with 'commit', meaning the object contians information about a commit
                rawData = zlib.decompress(f.read())
                if rawData.startswith(b'commit '):
                    #get the commit hash by hashing the git object using sha1
                    hash = hashlib.sha1(rawData).hexdigest()
                    t = commitNode(hash)
                    commitData = rawData.decode('utf-8').split('\n')

                    #gettting all the parent commits and adding it to the commit node 
                    for line in commitData:
                        if line.startswith('parent'):
                            t.parents.append(line[7:])
                    commitNodes[hash] = t
    
    # add all the branches to the corresponding commit nodes 
    for head in heads:
        curHash = heads[head]
        commitNodes[curHash].heads.append(head)
    
    #getting all the legit hashs, aka the ones that can be readed with a branch
    #to achieve this, we create a new heads dictionary that we are going to go down one by one,
    #adding all the hashs we find along the way to a set for no repeats. Also, if we are ever 
    #at a merge point, we can just go down one branch and add the other as a 'head' to traverse down later 
    heads2 = dict(heads)
    tempHeads = list(heads.keys())
    legitHashs = set()
    for head in tempHeads:
        curHash = heads2[head]
        while True:
            legitHashs.add(curHash)
            #if more than 1 parent, aka a merge, create a 'branch' for every parent besides the first one using hash + h as the head name
            if len(commitNodes[curHash].parents) > 1:
                for parent in commitNodes[curHash].parents[1:]:
                    newHead = parent + 'h'
                    tempHeads.append(newHead)
                    heads2[newHead] = parent
            #travel down the first parent, if no parents, we've reached the end of the branch, break
            if len(commitNodes[curHash].parents) > 0:
                curHash = commitNodes[curHash].parents[0]
            else:
                break
    
    # add all the children to the commit nodes that are legit, aka reachable with a branch      
    for hash in legitHashs:
        node = commitNodes[hash]
        if not len(node.parents) == 0:
            #going through the parents of all the nodes, and adding the child to the parents 
            for parent in node.parents:
                commitNodes[parent].children.append(node.commitHash)
    return commitNodes
    
#get all the heads in the .git/refs/heads folder and store them in a dictionary, with the head name as branch, hash as item 
def getHead():
    currentPath = getPath()
    heads = {}
    refsFolder = os.path.join(currentPath, ".git", "refs", "heads")
    for root, dirs, files in os.walk(refsFolder):
        for file in files:
            filePath = os.path.join(root, file)
            with open(filePath, 'r') as f:
                heads[file] = f.read().strip()
    return heads


def printBranch(commitNodes, commit, stickyCheck=False):
    curHash = commit
    while True:
        branchNames = ''
        # since we remove sever the link between parent and child when we are travelling down a path, if the node still have children
        # that means there was a branch that we've just finished traveling, down, and we need to go down another branch,
        #therefore print the sticky end, remembering not to print the branch names for the sticky end 
        if len(commitNodes[curHash].children) > 0:
            print(curHash,'=',sep='')
            print()
            return curHash
        
        #printing the current hash with branch names, if stickycheck == true, that means the this the beginning of a new section,
        #set branch names to '' because we don't want to print them in that case 
        for h in commitNodes[curHash].heads:
            branchNames = branchNames + " " + h
        if stickyCheck:
            branchNames = ''
            stickyCheck = False
        print(curHash, branchNames, sep='')
        
        # more than 1 parent == merge 
        if len(commitNodes[curHash].parents) > 1:
            commitNodes[curHash].mergeStartingPoint += 1
        if len(commitNodes[curHash].parents) > 0:
            # if there are parents, that means we are going to continue traversing the branch 
            # when we've decided to travel down a path, we are going to sever the connection between the two nodes
            # this way, we can essentially remove branches after we finished printing them, until there is only one branch left 
            # and we print till the finish line
            commitNodes[commitNodes[curHash].parents[0]].children.remove(curHash)
            nextParent = commitNodes[curHash].parents[0]
            del commitNodes[curHash].parents[0]
            curHash = nextParent
        else:
            # if no parents of node, that means we've reached the root node 
            return curHash

def getStartingHead(commitNodes, commit):
    while True:
        if len(commitNodes[commit].children) > 0:
            lastCommit = commit
            commit = commitNodes[commit].children[0]
            #making sure that the first item in the list of parents is the commit we just came from, so we go back down in the expected direction
            commitNodes[commit].parents.remove(lastCommit)
            commitNodes[commit].parents.insert(0, lastCommit)
        else:
            return commit          
            


def topo_order_commits():
    heads = getHead()
    commitNodes = getCommitNodes(heads)
    
    #we want starting head to be the "tip of a branch", and not in the middle of another branch. We check for this by looking
    #at how many children a particular head have
    startingHead = ''
    for head in heads:
        curHash = heads[head]
        if not len(commitNodes[curHash].children) == 0:
            continue
        startingHead = curHash
    
    stickyCheck = False 
    while True:
        endHash = printBranch(commitNodes, startingHead,stickyCheck)
        if len(commitNodes[endHash].children) > 0:
            startingHead = getStartingHead(commitNodes, endHash)
            if commitNodes[startingHead].mergeStartingPoint > 0:
                commitNodes[startingHead].mergeStartingPoint -= 1
                print('=',end="")
                stickyCheck = True
            else:
                print('=')
                stickyCheck = False
        else:
            return
    




if __name__ == '__main__':
    topo_order_commits()

