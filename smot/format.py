from __future__ import annotations
from typing import (
    List,
    Optional,
    Tuple,
    Union,
)

from smot.classes import Node, Tree, makeTree, AnyNode, AnyNodeData
import smot.algorithm as alg
import re


def quote(x: str) -> str:
    if "'" in x:
        # escape any double quotes
        x = re.sub('"', '\\"', x)
        # double quote the expression
        x = f'"{x}"'
    else:
        # if there are no internal single quotes, single quote everything
        x = f"'{x}'"
    return x


def quoteIf(x: str) -> str:
    if set("^,:;()[]'\"").intersection(set(x)):
        return quote(x)
    else:
        return x


def newick(node: Union[Tree, AnyNode]) -> str:
    if isinstance(node, Tree):
        node_obj = node.tree
    else:
        node_obj = node

    return _newick(node_obj) + ";"


def _newick(node: AnyNode) -> str:
    # allow input to be a Tree object
    if isinstance(node, Tree):
        node = node.tree
    if node.kids:
        s = "(" + ",".join([_newick(kid) for kid in node.kids]) + ")"
    else:
        s = ""
    if node.data.label:
        label = node.data.label
        if node.data.form or set("^,:;()[]'\"").intersection(set(label)):
            label = quote(label)
        s += label
    if node.data.form:
        form_str = ",".join([k + "=" + quoteIf(v) for (k, v) in node.data.form.items()])
        s += "[&" + form_str + "]"
    if node.data.length is not None:
        s += ":" + "{:0.3g}".format(node.data.length)
    return s


def nexus(treeOrNode: Union[AnyNode, Tree]) -> str:
    # allow input to be a Node object
    if isinstance(treeOrNode, Node):
        tree = makeTree(tree=treeOrNode)
    else:
        tree = treeOrNode

    def _fun(
        b: List[Tuple[str, Optional[str]]], x: AnyNodeData
    ) -> List[Tuple[str, Optional[str]]]:
        if x.isLeaf:
            # if colors were set by grep, they will be stored here and they
            # should over-ride the default colors
            if x.labelColor:
                color = x.labelColor
            # colors from the input nexus file
            elif x.label in tree.colmap:
                color = tree.colmap[x.label]
            # no colors are available
            else:
                color = None
            b.append((x.label, color))
        return b

    s = ["#NEXUS"]
    if tree.colmap:
        colortips: List[Tuple[str, Optional[str]]]
        colortips = alg.treefold(tree.tree, _fun, [])
        s.append("begin taxa;")
        s.append(f"\tdimensions ntax={str(len(colortips))};")
        s.append("\ttaxlabels")
        for (tip, color) in sorted(colortips):
            if color is not None:
                color_str = f"[&!color={color}]"
            else:
                color_str = ""
            s.append(f"\t{quote(tip)}{color_str}")
        s.append(";")
        s.append("end;\n")
    s.append("begin trees;")
    s.append(f"\ttree tree_1 = [&R] {newick(tree)}")
    s.append("end;\n")
    for (k, vs) in tree.meta.items():
        s.append(f"begin {k};")
        for v in vs:
            s.append(f"\t{v};")
        s.append("end;\n")
    return "\n".join(s)
