import re


class Tree:
    def __init__(self, tree, colmap=dict(), meta=dict()):
        self.tree = tree
        self.meta = meta

    def newick(self):
        return self.tree.newick()

    def __str__(self):
        # FIXME: currently this just wraps the newick function
        # I should instead write nexus format with coloring and all
        return str(self.tree)


class NodeData:
    def __init__(self, label=None, form=None, length=None, factor=None, isLeaf=False):
        self.label = label
        self.form = form
        self.length = length
        self.factor = factor
        self.nleafs = None
        self.factorCount = None
        self.factorDist = dict()
        self.color = self._color()
        self.isLeaf = isLeaf

    def _color(self):
        color = None
        if self.label:
            m = re.search("&!color=(#\d{6})", self.label)
            if m:
                color = m.groups()[0]
        return color

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

    def newick(self):
        return str(self) + ";"

    def __eq__(self, other):
        return self.kids == other.kids and self.data == other.data

    def __str__(self):

        if self.kids:
            s = "(" + ",".join([str(kid) for kid in self.kids]) + ")"
        else:
            s = ""
        if self.data.label:
            label = self.data.label
            if self.data.form or set("^,:;()[]'\"").intersection(set(label)):
                if "'" in label:
                    # escape any double quotes
                    label = re.sub('"', '\\"', label)
                    # double quote the expression
                    label = f'"{label}"'
                else:
                    # if there are no internal single quotes, single quote everything
                    label = f"'{label}'"
            s += label
        if self.data.form:
            s += "[" + self.data.form + "]"
        if self.data.length is not None:
            s += ":" + "{:0.3g}".format(self.data.length)
        return s

    def __repr__(self):
        return str(self)
