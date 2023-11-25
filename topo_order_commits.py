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


def topo_order_commits():

    currentPath = getPath()
    heads = {}
    refsFolder = os.path.join(currentPath, ".git", "refs", "heads")
    for root, dirs, files in os.walk(refsFolder):
        for file in files:
            filePath = os.path.join(root, file)
            with open(filePath, 'r') as f:
                heads[file] = f.read().strip()
    
    commitNodes = {}

    objectsFolder = os.path.join(currentPath, ".git", "objects")
    # create all the commit nodes and add the parents
    for root, dirs, files in os.walk(objectsFolder):
        for file in files:
            filePath = os.path.join(root, file)

            with open(filePath, 'rb') as f:
                rawData = zlib.decompress(f.read())

                if rawData.startswith(b'commit '):
                    hash = hashlib.sha1(rawData).hexdigest()
                    t = commitNode(hash)
                    commitData = rawData.decode('utf-8').split('\n')

                    for line in commitData:
                        if line.startswith('parent'):
                            t.parents.append(line[7:])
                    commitNodes[hash] = t
    # add all the children to the commit nodes 
    for hash in commitNodes:
        node = commitNodes[hash]
        if not len(node.parents) == 0:
            for parent in node.parents:
                commitNodes[parent].children.append(node.commitHash)
    # add all the branches to the corresponding commit nodes 
    for head in heads:
        curHash = heads[head]
        commitNodes[curHash].heads.append(head)
    
    for head in heads:
        if heads[head] == None:
            continue
        curHash = heads[head]
        if not len(commitNodes[curHash].children) == 0:
            continue
        
        branchNames = ''
        for h in commitNodes[curHash].heads:
            branchNames = branchNames + " " + h
        print(curHash, " ", branchNames)
        while True:
            node = commitNodes[curHash]
            if not len(node.parents) == 0:
                for parent in node.parents:
                    curHash = parent
                branchNames = ""
                if not len(commitNodes[curHash].heads) == 0:
                    for h in commitNodes[curHash].heads:
                        branchNames = branchNames + " " + h
                        heads[h] = None
                        
                print(curHash + branchNames)
            else:
                break



if __name__ == '__main__':
    topo_order_commits()

