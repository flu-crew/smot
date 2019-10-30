from src.classes import Node
from collections import Counter

"""
Map a function over the data (label, format, and branch length) of each node in
the tree. The function is guaranteed to never alter the topology of the tree.

fun :: NodeData -> NodeData
"""
def treemap(node, fun, **kwargs):
    node.data = fun(node.data, **kwargs)
    node.kids = [treemap(k, fun, **kwargs) for k in node.kids]
    return node


"""
fun :: a -> NodeData -> a
"""
def treefold(node, fun, init, **kwargs):
    x = fun(init, node.data, **kwargs)
    for kid in node.kids:
        x = treefold(kid, fun, x, **kwargs)
    return x

"""
fun :: Node -> Node
"""
def treecut(node, fun, **kwargs):
    node.kids = fun(node, **kwargs)
    node.kids = [treecut(kid, fun, **kwargs) for kid in node.kids]
    return node


"""
Assign factors to nodes based on the node label string
"""
def factorByLabel(node, fun, **kwargs):
    def mapfun(ndata, **kwargs):
        ndata.factor = fun(ndata.label, **kwargs)
        return ndata
    return treemap(node, mapfun, **kwargs)

def countFactors(node):
    def fun_(b, x):
        if x.factor:
            b.append(x.factor)
        return b
    factors = treefold(node, fun_, [])
    return Counter(factors)


"""
Recurse down a tree, returning the leftmost leaf
"""
def getLeftmost(node):
    if node.kids:
        return getLeftmost(node.kids[0])
    else:
        return node


def chooseN(node, n): 
    if n == 0:
        return None
    if not node.nleafs:
        node = setNLeafs(node)
    if not node.kids:
        if n == 1:
            return node
        else:
            raise "Bug in chooseN"
    else:
        N = sum([kid.nleafs for kid in node.kids])
        selection = distribute(N, len(kid.nleafs), [kid.nleafs for kid in node.kids])
        node.kids = [chooseN(kid, m) for kid,m in zip(node.kids, selection) if m > 0]

def distribute(count, groups, sizes=None):
    """
    Break n into k groups

    For example:

    distribute(5, 3) --> [2, 2, 1]
    distribute(1, 3) --> [1, 0, 0]
    distribute(2, 2) --> [1, 1]

    If the argument 'sizes' is given, then elements are selected from a pool of
    'sizes' things.  Thus there is an upper limit on how many items can be
    selected. For example:

    distributed(10, 3, [1, 4, 4]) --> [1,4,4]
    distributed(10, 3, [1, 5, 5]) --> [1,5,4]
    distributed(5, 3, [1, 1, 1]) --> [1,1,1]
    distributed(5, 3, [1, 1, 1]) --> [1,1,1]
    distributed(5, 3, [0, 10, 1]) --> [0,4,1]
    """
    if not sizes:
        sizes = [count] * groups

    unfilledGroups = sum(s > 0 for s in sizes)
    
    if count <= unfilledGroups:
        selection = []
        for i in range(groups):
            if count > 0 and sizes[i] > 0:
                selection.append(1)
                count -= 1
            else:
                selection.append(0)
    else:
        selection = []
        for i in range(groups):
            selection.append(min(count // unfilledGroups, sizes[i]))
            sizes[i] -= selection[i]
        remaining = count - sum(selection)
        if remaining > 0 and any(s > 0 for s in sizes):
            remaining_selection = distribute(remaining, groups, sizes)
            selection = [s1 + s2 for s1,s2 in zip(selection, remaining_selection)]
    return selection

def setNLeafs(node):
    if not node.kids:
        node.nleafs = 1
    else:
        node.kids = [setNLeafs(kid) for kid in node.kids] 
        node.nleafs = sum(kid.nleafs for kid in node.kids)
    return node


def sampleContext(node, keep=[], maxTips=5):
    newkids = []
    for kid in node.kids:
        factorCount = countFactors(kid)
        if len(factorCount) == 1 and list(factorCount.values())[0] >= maxTips:
            if list(factorCount.keys())[0] in keep:
                newkids.append(kid)
            else:
                newkids.append(getLeftmost(kid))
        else:
            newkids.append(sampleContext(kid, keep=keep, maxTips=maxTips))
    node.kids = newkids
    return node
