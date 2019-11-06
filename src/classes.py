import re
from Bio.Phylo.BaseTree import Clade

class NodeData:
    def __init__(self, label=None, form=None, length=0, factor=None, isLeaf=False):
        self.label = label
        self.form = form
        if not length:
            self.length = 0 
        else:
            self.length = length
        self.factor = factor
        self.nleafs = None
        self.color = None
        self.isLeaf = isLeaf

    def _color(self):
        m = re.match("&!color=(#\d{6})")
        if m:
            self.color = m.groups(1)

    def __eq__(self, other):
        # Equality is based off intrinsic data of the tree, not internal data,
        # such as factor.
        return (
            self.label == other.label
            and self.form == other.form
            and self.length == other.length
        )

class Node:
    def __init__(self, kids=[], nleafs = None, **kwargs):
        self.kids = kids
        self.data = NodeData(**kwargs, isLeaf = not bool(kids))
        self.nleafs = nleafs

    def newick(self):
         return str(self) + ";"

    def asBiopythonTree(self):
        return Clade(
            branch_length = self.data.length,
            name = self.data.label,
            color = self.data.color,
            clades = [kid.asBiopythonTree() for kid in self.kids]
        )

    def __eq__(self, other):
        return self.kids == other.kids and self.data == other.data

    def __str__(self):
        if self.kids:
            s = "(" + ",".join([str(kid) for kid in self.kids]) + ")"
        else:
            s = ""
        if self.data.label:
            if set("^,:;()[]'\"").intersection(set(self.data.label)):
                if "'" in self.data.label:
                    if '"' in self.data.label:
                        label = re.sub('"', '\\"', self.data.label) 
                        s += f'"{label}"'
                    else:
                        s += f'"{self.data.label}"'
                elif '"' in self.data.label:
                    s += f"'{self.data.label}'"
            else:
                s += self.data.label
        if self.data.form:
            s += "[" + self.data.form + "]"
        if self.data.length:
            if (self.data.length - int(self.data.length)) == 0:
                s += ":" + str(int(self.data.length))
            else:
                s += ":" + str(self.data.length)
        else:
            s += ":0"
        return s

    def __repr__(self):
        return str(self)
