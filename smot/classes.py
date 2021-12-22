from typing import Optional, Dict, List, Generic, TypeVar, Any
from collections import Counter, defaultdict

F = TypeVar("F", None, Optional[str], str) 
LC = TypeVar("LC", None, int)
FC = TypeVar("FC", None, Counter)
BL = TypeVar("BL", None, Optional[float], float)

class Tree():
    def __init__(
        self, colmap: Dict[str, str] = dict(), meta: Dict[str, str] = dict()
    ):
        self.meta : Dict[str, str] = meta
        self.colmap : Dict[str, str] = colmap
        self.tree : Any

class NodeData(Generic[F,LC,FC,BL]):
    def __init__(self, label, form, length, isLeaf=False):
        self.label = label
        if not form:
            self.form = dict()
        else:
            self.form = form
        self.length : BL = length
        self.isLeaf = isLeaf
        self.factor : F
        self.nleafs : LC
        self.factorCount : FC
        self.factorDist : Dict[str, float]
        self.labelColor : Dict[str, str]

    def __eq__(self, other):
        # Equality is based off intrinsic data of the tree, not internal data,
        # such as factor.
        return (
            self.label == other.label
            and self.form == other.form
            and self.length == other.length
        )



class Node(Generic[F, LC, FC, BL]):
    index = 0

    def __init__(self, kids : List[Node[F, LC, FC, BL]], data : NodeData[F, LC, FC, BL]):
        self.kids : List[Node[F, LC, FC, BL]] = kids
        self.data : NodeData[F, LC, FC, BL] = data


    def __eq__(self, other):
        return self.kids == other.kids and self.data == other.data


def make_Tree(node : Node[F, LC, FC, BL], colmap: Dict[str, str] = dict(), meta: Dict[str, str] = dict()) :
    tree = Tree(colmap, meta)
    tree.tree = node 
    return tree


def make_Node(
    kids : List[Node[None, None, None, Optional[float]]] = [],
    label : Optional[str] = None,
    form : Optional[Dict[str,str]] = None,
    length : Optional[float] = None
  ) -> Node[None,None,None,Optional[float]]:
  return Node(kids, make_NodeData(label=label, form=form, length=length, isLeaf=not bool(kids)))


def make_NodeData(label : Optional[str], form : Optional[Dict[str,str]], length : Optional[float], isLeaf : bool) -> NodeData[None,None,None,Optional[float]]:
    nd : NodeData[None,None,None,Optional[float]] = NodeData(label=label, form=form, length=length, isLeaf=isLeaf)
    nd.factor = None
    nd.nleafs = None
    nd.factorCount = None
    nd.factorDist = dict()
    nd.labelColor = dict()
    return nd
