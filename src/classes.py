class NodeData:
    def __init__(self, label=None, form=None, length=None, factor=None):
        self.label = label
        self.form = form
        self.length = length
        self.factor = factor
        self.nleafs = None

    def __eq__(self, other):
        # Equality is based off intrinsic data of the tree, not internal data,
        # such as factor.
        return (
            self.label == other.label
            and self.form == other.form
            and self.length == other.length
        )


class Node:
    def __init__(self, kids=[], **kwargs):
        self.kids = kids
        self.data = NodeData(**kwargs)

    def __eq__(self, other):
        return self.kids == other.kids and self.data == other.data

    def __str__(self):
        if self.kids:
            s = "(" + ",".join([str(kid) for kid in self.kids]) + ")"
        else:
            s = ""
        if self.data.label:
            s += self.data.label
        if self.data.form:
            s += "[" + self.data.label + "]"
        if self.data.length:
            s += ":" + self.data.length
        return s

    def __repr__(self):
        return str(self)
