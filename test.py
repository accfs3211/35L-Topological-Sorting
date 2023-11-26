
def func(dic):
    dic["key"] = 1

x = {}
x['key'] = 0
func(x)
print(x['key'])