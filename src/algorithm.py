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
