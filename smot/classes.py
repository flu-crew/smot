import re


class Tree:
    def __init__(self, tree, colmap=dict(), meta=dict()):
        self.tree = tree
        self.meta = meta
        self.colmap = colmap


class NodeData:
    def __init__(self, label=None, form=None, length=None, factor=None, isLeaf=False):
        self.label = label
        if not form:
            self.form = dict()
        else:
            self.form = form
        self.length = length
        self.factor = factor
        self.nleafs = None
        self.factorCount = None
        self.factorDist = dict()
        self.labelColor = None
        self.isLeaf = isLeaf

    def __eq__(self, other):
        # Equality is based off intrinsic data of the tree, not internal data,
        # such as factor.
        return (
            self.label == other.label
            and self.form == other.form
            and self.length == other.length
        )


class Node:
    index = 0

    def __init__(self, kids=[], **kwargs):
        self.kids = kids
        self.data = NodeData(**kwargs, isLeaf=not bool(kids))

    def __eq__(self, other):
        return self.kids == other.kids and self.data == other.data
