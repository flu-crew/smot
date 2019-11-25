from smot.classes import Node
from smot.util import log, die
from collections import Counter, defaultdict
import re
import sys
import math
import random


def treemap(node, fun, **kwargs):
    """
    Map a function over the data (label, format, and branch length) of each node in
    the tree. The function is guaranteed to never alter the topology of the tree.

    fun :: NodeData -> NodeData
    """
    node.data = fun(node.data, **kwargs)
    node.kids = [treemap(k, fun, **kwargs) for k in node.kids]
    return node


def treefold(node, fun, init, **kwargs):
    """
    fun :: a -> NodeData -> a
    """
    x = fun(init, node.data, **kwargs)
    for kid in node.kids:
        x = treefold(kid, fun, x, **kwargs)
    return x


def treecut(node, fun, **kwargs):
    """
    fun :: Node -> Node
    """
    node.kids = fun(node, **kwargs)
    node.kids = [treecut(kid, fun, **kwargs) for kid in node.kids]
    return node


def clean(tree, isRoot=True):
    """
    Remove nodes that have only one child. Add the branch lengths.
    """

    def _clean(node, isRoot):
        # remove empty children
        node.kids = [kid for kid in node.kids if kid.data.nleafs > 0]
        # remove all single-child nodes
        while len(node.kids) == 1:
            if node.data.length is not None and node.kids[0].data.length is not None:
                node.kids[0].data.length += node.data.length
            node = node.kids[0]
            # remove empty children
            node.kids = [kid for kid in node.kids if kid.data.nleafs > 0]
        # clean all children
        newkids = []
        for kid in node.kids:
            kid = _clean(kid, False)
            if kid.data.isLeaf or kid.kids:
                newkids.append(kid)
        node.kids = newkids
        # if `tree` is the entire tree and if the tree contains only one leaf, then
        # we need to insert a root node
        if node.data.isLeaf and isRoot:
            node = Node(kids=[node])
        return node

    tree = setNLeafs(tree)
    return _clean(tree, isRoot)


def factorByLabel(node, fun, **kwargs):
    """
    Assign factors to nodes based on the node label string
    """

    def mapfun(ndata, **kwargs):
        ndata.factor = fun(ndata.label, **kwargs)
        return ndata

    return treemap(node, mapfun, **kwargs)


def factorByField(tree, field, default=None, sep="|"):
    """
    Factor by the <field>th 1-based index in the tip label.
    """

    def _fun(name):
        try:
            return name.split(sep)[field - 1]
        except:
            return default

    return factorByLabel(tree, _fun)


def factorByCapture(tree, pat, default=None):
    pat = re.compile(pat)

    def _fun(name):
        if name:
            m = re.search(pat, name)
            if m:
                if m.groups(1):
                    if isinstance(m.groups(1), str):
                        return m.groups(1)
                    else:
                        return m.groups(1)[0]
                else:
                    return m.groups(0)
        return default

    return factorByLabel(tree, _fun)


def factorByTable(tree, filename, default=None):
    with open(filename, "r") as f:
        factorMap = dict()
        for line in f.readlines():
            try:
                (k, v) = line.strip().split("\t")
                factorMap[k] = v
            except ValueError:
                print("Expected two columns in --factor-by-table file", file=sys.stderr)
                sys.exit(1)

        def _fun(name):
            if name:
                for k, v in factorMap.items():
                    if k in name:
                        return v
            return default

        return factorByLabel(tree, _fun)


def isMonophyletic(node):
    """
    Check is a branch is monophyletic relative to the defined factors. Assumes
    that `setFactorCounts` has been called on the tree.
    """
    return len(node.data.factorCount) <= 1


def getFactor(node):
    if node.data.factorCount:
        return list(node.data.factorCount.keys())[0]
    else:
        return None


def imputeFactors(tree):
    def setFactors(node, factor):
        def _fun(b):
            b.factor = factor
            return b

        return treemap(node, _fun)

    if tree.data.factorCount and isMonophyletic(tree):
        tree = setFactors(tree, getFactor(tree))
    else:
        newkids = [imputeFactors(kid) for kid in tree.kids]
        tree.kids = newkids
    return tree


def getLeftmost(node):
    """
    Recurse down a tree, returning the leftmost leaf
    """
    if node.kids:
        return getLeftmost(node.kids[0])
    else:
        return node


def sampleN(node, n):
    if not node.data.nleafs:
        node = setNLeafs(node)
    if n == 0:
        raise "Cannot create empty leaf"
    elif n > node.data.nleafs:
        return node
    if not node.kids and not n == 1:
        raise "Bug in sampleN"
    N = sum([kid.data.nleafs for kid in node.kids])
    selection = distribute(n, len(node.kids), [kid.data.nleafs for kid in node.kids])
    node.kids = [sampleN(kid, m) for kid, m in zip(node.kids, selection) if m > 0]
    if len(node.kids) == 1:
        if node.kids[0].data.length is not None and node.data.length is not None:
            node.kids[0].data.length += node.data.length
        node = node.kids[0]
    return node


def sampleRandom(node, n, rng):
    """
    Sample N random tips from node 
    """
    if not node.data.nleafs:
        node = setNLeafs(node)
    if n == 0:
        raise "Cannot create empty leaf"
    elif n > node.data.nleafs:
        return node
    if not node.kids and not n == 1:
        raise "Bug in sampleN"

    def _collect(b, d):
        if d.isLeaf:
            b.add(d.label)
        return b

    labels = treefold(node, _collect, set())

    # The set datastructure is a hash table. Hashes of strings vary between
    # python sessions. Thus the sorting of elements in a set will also vary
    # between sessions. So before sampling, the set needs to be converted to a
    # list of sorted. Otherwise, the selected labels will be random even given
    # the same random seed.
    chosen = rng.sample(sorted(list(labels)), n)

    def _cull(node):
        chosenOnes = [
            kid
            for kid in node.kids
            if (not kid.data.isLeaf) or (kid.data.label in chosen)
        ]
        return chosenOnes

    sampledTree = treecut(node, _cull)
    sampledTree = clean(sampledTree)
    sampledTree = setNLeafs(sampledTree)
    return sampledTree


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
            selection = [s1 + s2 for s1, s2 in zip(selection, remaining_selection)]
    return selection


def setNLeafs(node):
    if node.data.isLeaf:
        node.data.nleafs = 1
    else:
        node.kids = [setNLeafs(kid) for kid in node.kids]
        node.data.nleafs = sum(kid.data.nleafs for kid in node.kids)
    return node


def setFactorCounts(node):
    if node.data.isLeaf:
        if node.data.factor:
            node.data.factorCount = Counter([node.data.factor])
        else:
            node.data.factorCount = Counter()
    else:
        node.data.factorCount = Counter()
        node.kids = [setFactorCounts(kid) for kid in node.kids]
        node.data.factorCounts = Counter()
        for kid in node.kids:
            node.data.factorCount += kid.data.factorCount

    return node


def sampleContext(tree, keep=[], maxTips=5):
    # recursive sampler
    def _sampleContext(node):
        newkids = []
        for kid in node.kids:
            if (
                len(kid.data.factorCount) == 1
                and list(kid.data.factorCount.values())[0] >= maxTips
            ):
                if list(kid.data.factorCount.keys())[0] in keep:
                    newkids.append(kid)
                else:
                    newkids.append(sampleN(kid, maxTips))
            else:
                newkids.append(_sampleContext(kid))
        node.kids = newkids
        return node

    tree = setNLeafs(tree)
    tree = setFactorCounts(tree)
    return clean(_sampleContext(tree))


def sampleParaphyletic(tree, proportion=0.5, keep=[], minTips=3, seed=None):
    rng = random.Random(seed)

    def getLabels(node):
        def _collect(b, d):
            if d.isLeaf:
                b.add(d.label)
            return b

        return treefold(node, _collect, set())

    def sampleLabels(labels, factor):
        if factor in keep:
            return labels
        else:
            N = min(len(labels), max(minTips, math.ceil(proportion * len(labels))))
            try:
                sample = rng.sample(sorted(list(labels)), N)
            except ValueError:
                log(f"Bad sample size ({N}) for population of size ({len(labels)})")
                sys.exit(1)
            return sample

    def _select(node, selected, paraGroup, paraFactor):
        rebelChild = None
        potentialMembers = []
        canMerge = True
        oldFactor = paraFactor
        for kid in node.kids:
            factor = getFactor(kid)
            if not canMerge:
                potentialMembers.append(kid)
            else:
                if isMonophyletic(kid):
                    if factor == paraFactor or factor is None:
                        potentialMembers.append(kid)
                    elif (
                        factor != paraFactor
                        and factor != oldFactor
                        and paraFactor != oldFactor
                    ):
                        canMerge = False
                        potentialMembers.append(kid)
                    else:
                        selected.update(sampleLabels(paraGroup, paraFactor))
                        paraGroup = getLabels(kid)
                        paraFactor = factor
                else:
                    if rebelChild is None:
                        rebelChild = kid
                    else:
                        canMerge = False
                        selected.update(sampleLabels(paraGroup, paraFactor))
                        paraFactor = None
                        paraGroup = set()
                        selected.update(_select(rebelChild, selected, set(), None))
                        selected.update(_select(kid, selected, set(), None))
        if canMerge and rebelChild is not None:
            for k in potentialMembers:
                paraGroup.update(getLabels(k))
            selected.update(_select(rebelChild, selected, paraGroup, paraFactor))
        else:
            groups = defaultdict(set)
            for k in potentialMembers:
                factor = getFactor(k)
                if isMonophyletic(k):
                    if factor == paraFactor or factor is None:
                        paraGroup.update(getLabels(k))
                    else:
                        groups[factor].update(getLabels(k))
                else:
                    selected.update(_select(k, selected, set(), None))
            selected.update(sampleLabels(paraGroup, paraFactor))
            for (k, v) in groups.items():
                selected.update(sampleLabels(v, factor=k))
        return selected

    tree = setFactorCounts(tree)
    selected = _select(tree, set(), set(), None)

    def _cull(node):
        chosenOnes = [
            kid
            for kid in node.kids
            if (kid.data.isLeaf and (kid.data.label in selected)) or kid.kids
        ]
        return chosenOnes

    sampledTree = treecut(tree, _cull)
    sampledTree = clean(sampledTree)
    return sampledTree


def sampleProportional(tree, proportion=0.5, keep=[], minTips=3, seed=None):
    rng = random.Random(seed)

    def _sample(kid):
        N = max(minTips, math.floor(kid.data.nleafs * proportion))
        return sampleRandom(kid, N, rng=rng)

    # recursive sampler
    def _sampleProportional(node):
        newkids = []
        for kid in node.kids:
            nfactors = len(kid.data.factorCount)
            if nfactors == 0:
                newkids.append(_sample(kid))
            elif nfactors == 1:
                if list(kid.data.factorCount.keys())[0] in keep:
                    newkids.append(kid)
                else:
                    newkids.append(_sample(kid))
            else:
                newkids.append(_sampleProportional(kid))
        node.kids = newkids
        return node

    if not (0 <= proportion <= 1):
        die("Expected parameter 'proportion' to be a number between 0 and 1")
    if not (0 <= minTips and minTips % 1 == 0):
        die("Expected parameter 'minTips' to be a positive integer")
    tree = setNLeafs(tree)
    tree = setFactorCounts(tree)
    return clean(_sampleProportional(tree))
