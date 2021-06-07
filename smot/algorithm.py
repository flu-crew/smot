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
    node.kids = [treemap(k, fun, **kwargs) for k in node.kids if k is not None]
    return node


def treefold(node, fun, init, **kwargs):
    """
    fun :: a -> NodeData -> a
    """
    x = fun(init, node.data, **kwargs)
    for kid in [k for k in node.kids if k is not None]:
        x = treefold(kid, fun, x, **kwargs)
    return x


def treecut(node, fun, **kwargs):
    """
    fun :: Node -> Node
    """
    node.kids = fun(node, **kwargs)
    node.kids = [treecut(k, fun, **kwargs) for k in node.kids if k is not None]
    return node


def treepull(node, fun, **kwargs):
    """
    Change parent based on children

    Can alter leafs, since they are treated as nodes without children.

    fun :: NodeData -> [NodeData] -> NodeData
    """
    if node.data.isLeaf:
        node.data = fun(node.data, [])
    else:
        node.kids = [treepull(kid, fun, **kwargs) for kid in node.kids if kid is not None]
        node.data = fun(node.data, [kid.data for kid in node.kids], **kwargs)
    return node


def treepush(node, fun, **kwargs):
    """
    Change children based on parent

    fun :: NodeData -> NodeData -> NodeData
    """

    if not node.data.isLeaf:
        for kid in node.kids:
            kid.data = fun(node.data, kid.data, **kwargs)
        node.kids = [treepush(kid, fun, **kwargs) for kid in node.kids]

    return node

def tips(node):
    def _fun(b, x):
        if x.isLeaf:
            b.append(x.label)
        return b
    return treefold(node, _fun, [])

def partition(xs, f):
    a = []
    b = []
    for x in xs:
        if f(x):
            a.append(x)
        else:
            b.append(x)
    return (a, b)


def clean(node, isRoot=True):
    """
    Remove nodes that have only one child. Add the branch lengths.
    """

    def _clean(node, isRoot):
        # remove empty children
        node.kids = [
            kid for kid in node.kids if kid is not None and kid.data.nleafs > 0
        ]
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

    node = setNLeafs(node)
    return _clean(node, isRoot)


def factorByLabel(node, fun, **kwargs):
    """
    Assign factors to nodes based on the node label string
    """

    def mapfun(ndata, **kwargs):
        ndata.factor = fun(ndata.label, **kwargs)
        return ndata

    return treemap(node, mapfun, **kwargs)


def factorByField(node, field, default=None, sep="|"):
    """
    Factor by the <field>th 1-based index in the tip label.
    """

    def _fun(name):
        try:
            return name.split(sep)[field - 1]
        except:
            return default

    return factorByLabel(node, _fun)


def factorByCaptureFun(name, pat, default=None):
    if name:
        m = re.search(pat, name)
        if m:
            if m.groups():
                # take the deepest match
                return [x for x in list(m.groups()) if x is not None][-1]
            else:
                return m.groups(0)
    return default


def factorByCapture(node, pat, default=None):
    pat = re.compile(pat)
    return factorByLabel(node, lambda x: factorByCaptureFun(x, pat, default=default))


def factorByTable(node, filename, default=None):
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

        return factorByLabel(node, _fun)


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


def imputeFactors(node):
    def setFactors(node, factor):
        def _fun(b):
            b.factor = factor
            return b

        return treemap(node, _fun)

    if node.data.factorCount and isMonophyletic(node):
        node = setFactors(node, getFactor(node))
    else:
        newkids = [imputeFactors(kid) for kid in node.kids]
        node.kids = newkids
    return node


def imputePatristicFactors(node):
    def kid_fun_(d, ds):
        d.factorDist = dict()
        if d.isLeaf and d.factor:
            d.factorDist[d.factor] = 0
        else:
            for kid_data in ds:
                for (label, dist) in kid_data.factorDist.items():
                    pdist = dist + kid_data.length
                    if label in d.factorDist:
                        d.factorDist[label] = min(pdist, d.factorDist[label])
                    else:
                        d.factorDist[label] = pdist
        return d

    def parent_fun_(p, k):
        for (label, dist) in p.factorDist.items():
            if label in k.factorDist:
                k.factorDist[label] = min(k.factorDist[label], dist + k.length)
            else:
                k.factorDist[label] = k.length + dist
        return k

    def leaf_fun_(d):
        if d.factorDist:
            d.factor = sorted(d.factorDist.items(), key=lambda x: x[1])[0][0]
        return d

    # pull the distances from child labels up to root
    node = treepull(node, kid_fun_)

    # push the distances from root down to leafs
    node = treepush(node, parent_fun_)

    # set factors to the nearest factor
    node = treemap(node, leaf_fun_)

    return node


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


def sampleRandom(node, rng, count_fun, keep_fun):
    """
    Sample N random tips from node
    """

    def _collect(b, d):
        if d.isLeaf:
            b.append(d.label)
        return b

    (keepers, samplers) = partition(treefold(node, _collect, []), keep_fun)

    # use the given function count_fun to decide how many tips to sample, but
    # never sample more than there are
    n = count_fun(samplers)

    # if we are sampling everything, just return the origin
    if n >= len(samplers):
        return node

    chosen = rng.sample(samplers, n)
    chosen = set(chosen + keepers)

    def _cull(node):
        chosenOnes = [
            kid for kid in node.kids if not kid.data.isLeaf or kid.data.label in chosen
        ]
        return chosenOnes

    sampledTree = treecut(node, _cull)
    sampledTree = clean(sampledTree)
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
    if not node:
      return node
    if node.data.isLeaf:
        node.data.nleafs = 1
    else:
        node.kids = [setNLeafs(kid) for kid in node.kids if kid is not None]
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
        for kid in node.kids:
            node.data.factorCount += kid.data.factorCount

    return node


def sampleContext(node, keep=[], maxTips=5):
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

    node = setNLeafs(node)
    node = setFactorCounts(node)
    return clean(_sampleContext(node))


def sampleParaphyletic(
    node, proportion=None, scale=None, number=None, keep=[], keep_regex="", minTips=3, seed=None
):
    rng = random.Random(seed)

    if proportion:

        def _sample(labels):
            return min(len(labels), max(minTips, math.ceil(proportion * len(labels))))

    elif scale:

        def _sample(labels):
            return min(len(labels), max(minTips, math.ceil(len(labels) ** scale)))

    else:

        def _sample(labels):
            return min(len(labels), number)
            

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
            if keep_regex:
                (keepers, samplers) = partition(
                    labels, lambda x: bool(re.search(keep_regex, x))
                )
            else:
                (keepers, samplers) = ([], labels)
            N = _sample(samplers)
            try:
                sample = rng.sample(sorted(list(samplers)), N)
            except ValueError:
                log(f"Bad sample size ({N}) for population of size ({len(labels)})")
                sys.exit(1)
            return sample + keepers

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

    node = setFactorCounts(node)
    selected = _select(node, set(), set(), None)

    def _cull(node):
        chosenOnes = [
            kid
            for kid in node.kids
            if (kid.data.isLeaf and (kid.data.label in selected)) or kid.kids
        ]
        return chosenOnes

    return clean(treecut(node, _cull))


def sampleProportional(
    node, proportion=None, scale=None, number=None, keep=[], keep_regex="", minTips=3, seed=None
):
    rng = random.Random(seed)

    if proportion:
        count_fun = lambda xs: max(minTips, math.floor(len(xs) * proportion))
    elif scale:
        count_fun = lambda xs: max(minTips, math.floor(len(xs) ** scale))
    else:
        count_fun = lambda xs: min(len(xs), number)

    if keep_regex:
        keep_fun = lambda label: re.search(keep_regex, label)
    else:
        keep_fun = lambda label: False

    def _sample(node):
        return sampleRandom(node=node, rng=rng, count_fun=count_fun, keep_fun=keep_fun)

    # recursive sampler
    def _sampleProportional(node):
        nfactors = len(node.data.factorCount)
        if(nfactors == 0):
          return _sample(node)
        elif nfactors == 1:
          if list(node.data.factorCount.keys())[0] in keep:
            return node
          else:
            node = _sample(node)
        else:
            node.kids = [_sampleProportional(kid) for kid in node.kids]
        return node

    node = setFactorCounts(node)
    return clean(_sampleProportional(node))


def colorTree(node, color):
    def fun_(d):
        d.form["!color"] = color
        return d

    return treemap(node, fun_)


def colorMono(node, colormap):
    if len(node.data.factorCount) == 1:
        label = list(node.data.factorCount.keys())[0]
        if label in colormap:
            node = colorTree(node, colormap[label])
    else:
        node.kids = [colorMono(kid, colormap) for kid in node.kids]
    return node


def filterMono(node, condition, action):
    if len(node.data.factorCount) == 1:
      if condition(node):
        node = action(node)
    else:
        node.kids = [filterMono(kid, condition, action) for kid in node.kids]
    return node


def intersectionOfSets(xss):
    try:
        x = set(xss[0])
        for y in xss[1:]:
            x = x.intersection(set(y))
    except:
        x = set()
    return x


def colorPara(node, colormap):
    if len(node.data.factorCount) == 1:
        label = list(node.data.factorCount.keys())[0]
        if label in colormap:
            node = colorTree(node, colormap[label])
    else:
        common = intersectionOfSets([k.data.factorCount.keys() for k in node.kids])
        if len(common) == 1:
            try:
                color = colormap[list(common)[0]]
                node = colorTree(node, colormap[list(common)[0]])
            except KeyError:
                pass
        node.kids = [colorPara(kid, colormap) for kid in node.kids]
    return node
