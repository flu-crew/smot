from __future__ import annotations
from typing import Optional, Dict, List, Generic, TypeVar, Any

from collections import Counter

F = TypeVar("F", None, Optional[str], str)
LC = TypeVar("LC", None, int)
FC = TypeVar("FC", None, Counter)
BL = TypeVar("BL", None, Optional[float], float)


class Tree:
    def __init__(self, colmap: Dict[str, str] = dict(), meta: Dict[str, str] = dict()):
        self.meta: Dict[str, str] = meta
        self.colmap: Dict[str, str] = colmap
        self.tree: Any


class NodeData(Generic[F, LC, FC, BL]):
    def __init__(self, label, form, length, isLeaf=False):
        self.label = label
        if not form:
            self.form = dict()
        else:
            self.form = form
        self.length: BL = length
        self.isLeaf = isLeaf
        self.factor: F
        self.nleafs: LC
        self.factorCount: FC
        self.factorDist: Dict[str, float]
        self.labelColor: Optional[str]

    def __eq__(self, other):
        # Equality is based off intrinsic data of the tree, not internal data,
        # such as factor.
        return (
            self.label == other.label
            and self.form == other.form
            and self.length == other.length
        )


AnyNodeData = NodeData[F, LC, FC, BL]
BaseNodeData = NodeData[Optional[str], None, None, Optional[float]]


class Node(Generic[F, LC, FC, BL]):
    index = 0

    def __init__(self):
        self.kids: List[AnyNode]
        self.data: AnyNodeData

    def __eq__(self, other):
        return self.kids == other.kids and self.data == other.data


AnyNode = Node[F, LC, FC, BL]
BaseNode = Node[Optional[str], None, None, Optional[float]]


def makeTree(
    tree: AnyNode,
    colmap: Dict[str, str] = dict(),
    meta: Dict[str, str] = dict(),
):
    x = Tree(colmap, meta)
    x.tree = tree
    return x


def makeNode(
    kids: List[BaseNode] = [],
    label: Optional[str] = None,
    form: Optional[Dict[str, str]] = None,
    length: Optional[float] = None,
    factor: Optional[str] = None,
) -> BaseNode:
    n: BaseNode = Node()
    n.kids = kids
    n.data = makeNodeData(
        label=label, form=form, length=length, isLeaf=not bool(kids), factor=factor
    )
    return n


def makeNodeData(
    label: Optional[str],
    form: Optional[Dict[str, str]],
    length: Optional[float],
    isLeaf: bool,
    factor: Optional[str] = None,
) -> BaseNodeData:
    nd: BaseNodeData = NodeData(label=label, form=form, length=length, isLeaf=isLeaf)
    nd.factor = factor
    nd.nleafs = None
    nd.factorCount = None
    nd.factorDist = dict()
    nd.labelColor = None
    return nd
