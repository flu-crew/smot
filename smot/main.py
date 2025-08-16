from __future__ import annotations
from typing import List, Optional, TextIO, Callable, Tuple, Dict, Counter

from smot.version import __version__
import click
import sys
from smot.classes import (
    Node,
    NodeData,
    Tree,
    AnyNode,
    AnyNodeData,
    LC,
    BL,
    makeNode,
    makeTree,
)
from smot.util import die
import smot.format as sf

INT_SENTINEL = 9999


def make_epilog(example):
    return f"For subcommand usage, append `-h` (e.g., {example} -h)"


class MaybeStringType(click.ParamType):
    name = "?str"

    def convert(self, value, param, ctx):
        if value is None:
            return None
        if value == "":
            return None
        try:
            return str(value)
        except TypeError:
            self.fail(
                "expected a string, got " f"{value!r} of type {type(value).__name__}",
                param,
                ctx,
            )


MaybeString = MaybeStringType()


class MaybeNatType(click.ParamType):
    name = "?nat"

    def convert(self, value, param, ctx):
        if value is None:
            return None
        if value == INT_SENTINEL:
            return None
        try:
            value = int(value)
        except TypeError:
            self.fail(
                "expected a int, got " f"{value!r} of type {type(value).__name__}",
                param,
                ctx,
            )
        if value < 1:
            self.fail(f"expected an integer greater than 1, got {value}")
        return value


MaybeNat = MaybeNatType()


class ListOfStringsType(click.ParamType):
    name = "[str]"

    def convert(self, value, param, ctx):
        try:
            if value is None:
                return []
            else:
                return [s.strip() for s in str(value).split(",")]
        except TypeError:
            self.fail(
                "expected a comma delimited string, got "
                f"{value!r} of type {type(value).__name__}",
                param,
                ctx,
            )


def checkColor(color: str) -> None:
    try:
        if color[0] != "#":
            die(f"Expected color hexcode to start with '#', got '{color}'")
        if len(color) != 7:
            die(
                f"Expected color hexcode to be 7 characters long (e.g., #080808), got '{color}'"
            )
    except IndexError:
        die(
            f"Expected color hexcode to be 7 characters long (e.g., #080808), got '{color}'"
        )


ListOfStrings = ListOfStringsType()

dec_default = click.option(
    "--default",
    type=str,
    default=None,
    help="The name to assign to tips that do not match a factor",
)


def factorTree(
    node: AnyNode,
    factor_by_capture: Optional[str] = None,
    factor_by_field: Optional[int] = None,
    factor_by_table: Optional[str] = None,
    default: Optional[str] = None,
    impute: bool = False,
    patristic: bool = False,
) -> Node[Optional[str], LC, Counter, BL]:
    import smot.algorithm as alg
    import re

    if factor_by_field is not None:
        field_index = factor_by_field
        if field_index < 1:
            die(
                f"Expected a positive integer for field --factor-by-field, got '{factor_by_field}'"
            )
        if default:
            die(
                "I'm sorry, I can't let you do that. Using --default with --factor-by-field is unsafe."
            )
        factoredNode = alg.factorByField(node, field_index)
    elif factor_by_capture is not None:
        pattern = re.compile(factor_by_capture)
        factoredNode = alg.factorByCapture(node, pat=pattern, default=default)
    elif factor_by_table is not None:
        with open(factor_by_table, "r") as fh:
            try:
                table = {
                    k: v
                    for (k, v) in [row.strip().split("\t") for row in fh.readlines()]
                }
            except ValueError:
                die("Expected two columns in --factor-by-table file")

            factoredNode = alg.factorByTable(node, table=table, default=default)
    else:
        factoredNode = node

    factoredCountedNode = alg.setFactorCounts(factoredNode)

    if patristic:
        return alg.imputePatristicFactors(factoredCountedNode)
    elif impute:
        return alg.imputeMonophyleticFactors(factoredCountedNode)
    else:
        return factoredCountedNode


def read_tree(treefile: TextIO) -> Tree:
    from smot.parser import read_fh

    return read_fh(treefile)


dec_tree = click.argument("TREE", default=sys.stdin, type=click.File())


#      smot tips [<filename>]
@click.command()
@dec_tree
def tips(tree: TextIO) -> None:
    """
    Print the tree tip labels. The order of tips matches the order in the tree
    (top-to-bottom).
    """
    import smot.algorithm as alg

    tree_obj = read_tree(tree)
    tree_obj.tree = alg.setNLeafs(tree_obj.tree)

    for tip in alg.tips(tree_obj.tree):
        print(tip)


def factoring(function):
    function = click.option(
        "--factor-by-capture",
        type=MaybeString,
        help="A regular expression with a capture for determining factors from labels",
    )(function)

    function = click.option(
        "--factor-by-field",
        type=MaybeNat,
        default=INT_SENTINEL,
        help="Factor by 1-based field index (with '|' delimiters, for now)",
    )(function)

    function = click.option(
        "--factor-by-table",
        type=MaybeString,
        help="Read factors from a TAB-delimited file (tip labels in the first column and factors in the second column)",
    )(function)

    return function


dec_proportion = click.option(
    "-p",
    "--proportion",
    type=click.FloatRange(min=0, max=1),
    help="The proportion of tips in a clade to keep",
)

dec_number = click.option(
    "-n",
    "--number",
    type=click.IntRange(min=0),
    help="The total number of tips to keep from each group",
)

dec_newick = click.option(
    "--newick",
    is_flag=True,
    help="Write output in simple newick format (tip colors and metadata will be lost)",
)

dec_scale = click.option(
    "-s",
    "--scale",
    type=click.FloatRange(min=1),
    help="Scale the size of the clade to this power (if there are n tips in a group, it will scale down to n^(1/r))",
)

dec_max_tips = click.option(
    "--max-tips",
    type=click.IntRange(min=0),
    default=5,
    help="Maximum number of tips to keep per unkept factor",
)

dec_min_tips = click.option(
    "--min-tips",
    type=click.IntRange(min=0),
    default=1,
    help="Minimum number of tips to keep per sampling group",
)

dec_seed = click.option("--seed", type=click.IntRange(min=1), help="Random seed")

dec_keep = click.option(
    "-k", "--keep", default=[], type=ListOfStrings, help="Factors to keep"
)

dec_keep_regex = click.option(
    "-r",
    "--keep-regex",
    default="",
    type=str,
    help="Keep all tips that match this pattern, these tips do not count towards downsampling quotas.",
)

dec_impute = click.option(
    "--impute",
    is_flag=True,
    default=False,
    help="Infer the monophyletic factor from context, if possible",
)

dec_patristic = click.option(
    "--patristic",
    is_flag=True,
    default=False,
    help="Infer factors by distance on the tree to the nearest label",
)


@click.command(name="equal")
@factoring
@dec_keep
@dec_default
@dec_max_tips
@click.option("--zero", is_flag=True, help="Set branches without lengths to 0")
@dec_newick
@dec_tree
def sample_equal_cmd(
    factor_by_capture: Optional[str],
    factor_by_field: Optional[int],
    factor_by_table: Optional[str],
    keep: List[str],
    default: Optional[str],
    max_tips: int,
    zero: bool,
    newick: bool,
    tree: TextIO,
) -> None:
    """

    Equal sampling. Descend from root to tip. At each node, determine if all
    descends have the same factor (is monophyletic). If the tree is not
    monophyletic, recurse into each subtree. If the tree is monophyletic, then
    sample N taxa from the tree.

    To sample N taxa from a tree with k immediate subtrees, divide N as evenly
    as possible into k groups. If a given subtree has fewer taxa than are
    alloted to it, then keep all taxa in the subtree and divide the remainder
    among its siblings. This partitioning is dependent on the ordering of the
    tree, so for reproducibility the tree should be sorted before sampling.

    Example:

      smot sample equal --factor-by-capture="(1B[^|]*)" --max-tips=5 1B.tre
    """

    import smot.algorithm as alg

    tree_obj = read_tree(tree)
    tree_obj.tree = factorTree(
        node=tree_obj.tree,
        factor_by_capture=factor_by_capture,
        factor_by_field=factor_by_field,
        factor_by_table=factor_by_table,
        default=default,
    )
    tree_obj.tree = alg.sampleEqual(tree_obj.tree, keep=keep, maxTips=max_tips)

    if newick:
        print(sf.newick(tree_obj))
    else:
        print(sf.nexus(tree_obj))


@click.command(name="mono")
@factoring
@dec_keep
@dec_keep_regex
@dec_default
@dec_min_tips
@dec_proportion
@dec_scale
@dec_number
@dec_seed
@dec_newick
@click.option("--zero", is_flag=True, help="Set branches without lengths to 0")
@dec_tree
def sample_mono_cmd(
    factor_by_capture: Optional[str],
    factor_by_field: Optional[int],
    factor_by_table: Optional[str],
    keep: List[str],
    keep_regex: str,
    default: Optional[str],
    min_tips: int,
    proportion: Optional[float],
    scale: Optional[float],
    number: Optional[int],
    seed: Optional[int],
    newick: bool,
    zero: bool,
    tree: TextIO,
) -> None:
    """
    Monophyletic sampling. Randomly sample --proportion of the tips (0 to 1)
    from each monophyletic subtree. Retain at least --min-tips tips in each
    branch.

    Monophyletic subtrees are identified by walking from root to tip and
    checking at each node whether all descendents have the same label (or no
    label).

    There is no requirement that each monophyletic subtree have a distinct
    label. Therefore, polyphyletic cases are also handled by this algorithm.

    Examples:
      \b
      # downsample to the max of 10% or 3 taxa from each clade in a 1B influenza tree 
      smot sample mono --factor-by-capture="(1B\.[^|]*)" -p 0.1 --min-tips=3 1B.tre

      \b
      # downsample each branch to the cube root (good when some clades are extremely large).
      smot sample mono --factor-by-capture="(1B\.[^|]*)" -s 3 --min-tips=3 1B.tre

      \b
      # downsample each branch to a random 3 members or fewer members
      smot sample mono --factor-by-capture="(1B\.[^|]*)" -s 3 1B.tre

      \b
      # downsample 1B tree but keep taxa with the pattern "202.-..-.." (taxa
      # from the 20s) in their labels or the factor "1B.1.1". 
      smot sample mono --factor-by-capture="(1B\.[^|]*)" -p 0.1 -r "202.-..-" -k "1B.1.2" --min-tips=3 1B.tre
    """

    import smot.algorithm as alg

    if not (proportion or scale or number):
        die("Please add either a --proportion or --scale or --number option")

    tree_obj = read_tree(tree)
    tree_obj.tree = factorTree(
        node=tree_obj.tree,
        factor_by_capture=factor_by_capture,
        factor_by_field=factor_by_field,
        factor_by_table=factor_by_table,
        default=default,
    )
    tree_obj.tree = alg.sampleMonophyletic(
        tree_obj.tree,
        keep=keep,
        keep_regex=keep_regex,
        proportion=proportion,
        scale=scale,
        number=number,
        minTips=min_tips,
        seed=seed,
    )

    if newick:
        print(sf.newick(tree_obj))
    else:
        print(sf.nexus(tree_obj))


@click.command(name="para")
@factoring
@dec_keep
@dec_keep_regex
@dec_default
@dec_min_tips
@dec_proportion
@dec_scale
@dec_number
@dec_seed
@dec_newick
@click.option("--zero", is_flag=True, help="Set branches without lengths to 0")
@dec_tree
def sample_para_cmd(
    factor_by_capture: Optional[str],
    factor_by_field: Optional[int],
    factor_by_table: Optional[str],
    keep: List[str],
    keep_regex: str,
    default: Optional[str],
    min_tips: int,
    proportion: Optional[float],
    scale: Optional[float],
    number: Optional[int],
    seed: Optional[int],
    newick: bool,
    zero: bool,
    tree: TextIO,
) -> None:
    """
    Paraphyletic sampling. The sampling algorithm starts at the root and
    descends to the tips. At each node, we store monophyletic subtrees in a
    list and descend into polyphyletic ones (whose leaves have multiple
    factors). If we reach a tip or encounter a monophyletic child of a
    different factor than the stored subtrees, then we stop and sample from all
    tips in the stored trees and initialize a new list with the new
    monophyletic child.

    Example:
      \b
      # Sample 10% of the members in each paraphyletic human or swine grouping
      smot sample para --factor-by-capture="(swine|human)" -p 0.1 --min-tips=5 pdm.tre

      \b
      # Sample the square root of the number of members in each paraphyletic
      # human or swine grouping
      smot sample para --factor-by-capture="(swine|human)" -s 2 --min-tips=5 pdm.tre

      \b
      # Sample 3 of the members in each paraphyletic human or swine grouping
      smot sample para --factor-by-capture="(swine|human)" -n 3 pdm.tre
    """

    import smot.algorithm as alg

    if not (proportion or scale or number):
        die("Please add either a --proportion or --scale or --number option")

    tree_obj = read_tree(tree)
    tree_obj.tree = factorTree(
        node=tree_obj.tree,
        factor_by_capture=factor_by_capture,
        factor_by_field=factor_by_field,
        factor_by_table=factor_by_table,
        default=default,
    )
    tree_obj.tree = alg.sampleParaphyletic(
        tree_obj.tree,
        keep=keep,
        keep_regex=keep_regex,
        proportion=proportion,
        scale=scale,
        number=number,
        minTips=min_tips,
        seed=seed,
    )

    if newick:
        print(sf.newick(tree_obj))
    else:
        print(sf.nexus(tree_obj))


@click.command()
@click.argument(
    "method", type=click.Choice(["table", "prepend", "append"], case_sensitive=False)
)
@factoring
@dec_default
@dec_impute
@dec_patristic
@dec_newick
@dec_tree
def factor(
    method: str,
    factor_by_capture: Optional[str],
    factor_by_field: Optional[int],
    factor_by_table: Optional[str],
    default: Optional[str],
    impute: bool,
    patristic: bool,
    newick: bool,
    tree: TextIO,
) -> None:
    """
    Impute, annotate with, and/or tabulate factors. The --impute option will
    fill in missing factors in monophyletic branches. This is useful, for
    example, for inferring clades given a few references in a tree. There are
    three modes: 'table' prints a TAB-delimited table of tip names and factors,
    'prepend' adds the factor to the beginning of the tiplabel (delimited with
    '|'), and 'append' adds it to the end.

    For example, to create a table of 1B clades: 

      smot factor table --factor-by-capture "(1B[^|]*)" 1B.tre
    """

    import smot.algorithm as alg

    tree_obj = read_tree(tree)
    tree_obj.tree = factorTree(
        node=tree_obj.tree,
        factor_by_capture=factor_by_capture,
        factor_by_field=factor_by_field,
        factor_by_table=factor_by_table,
        default=default,
        impute=impute,
        patristic=patristic,
    )

    # create TAB-delimited, table with columns for the tip labels and the
    # (possibly imputed) factor
    if method.lower() == "table":

        def _fun_treefold(b: List[str], x: AnyNodeData) -> List[str]:
            if x.isLeaf:
                if x.factor is None:
                    if default is None:
                        factor = ""
                    else:
                        factor = default
                else:
                    factor = x.factor
                b.append(f"{x.label}\t{factor}")
            return b

        row: str
        b: List[str] = []
        for row in alg.treefold(tree_obj.tree, _fun_treefold, b):
            print(row)

    # prepend or append the factor to the tip labels and print the resulting tree
    else:

        def _fun_treemap(x: NodeData) -> NodeData:
            if x.isLeaf:
                if x.factor is None:
                    x.factor = default
                if method.lower() == "prepend":
                    x.label = f"{x.factor}|{x.label}"
                else:
                    x.label = f"{x.label}|{x.factor}"
            return x

        tree_obj.tree = alg.treemap(tree_obj.tree, _fun_treemap)

        if newick:
            print(sf.newick(tree_obj))
        else:
            print(sf.nexus(tree_obj))


#      smot tipsed <pattern> <replacement> [<filename>]
@click.command()
@click.argument("PATTERN", type=str)
@click.argument("REPLACEMENT", type=str)
@dec_newick
@dec_tree
def tipsed(pattern: str, replacement: str, newick: bool, tree: TextIO) -> None:
    """
    Search and replace patterns in tip labels.
    """

    import smot.algorithm as alg
    import re

    pat = re.compile(pattern)

    def fun_(nodeData: AnyNodeData) -> AnyNodeData:
        if nodeData.label:
            nodeData.label = re.sub(pat, replacement, nodeData.label)
        return nodeData

    tree_obj = read_tree(tree)
    tree_obj.tree = alg.treemap(tree_obj.tree, fun_)
    tree_obj.colmap = {
        re.sub(pat, replacement, k): v for (k, v) in tree_obj.colmap.items()
    }

    if newick:
        print(sf.newick(tree_obj))
    else:
        print(sf.nexus(tree_obj))


@click.command()
@click.argument("PATTERN", type=str)
@click.option(
    "-v", "--invert-match", is_flag=True, help="Keep all leafs NOT matching the pattern"
)
@click.option(
    "-P", "--perl", is_flag=True, help="Interpret the pattern as a regular expression"
)
@click.option(
    "-f",
    "--file",
    is_flag=True,
    help="Read patterns from a file instead of a set string",
)
@dec_newick
@dec_tree
def grep(
    pattern: str, tree: TextIO, invert_match: bool, perl: bool, newick: bool, file: bool
):
    """
    Prune a tree to preserve only the tips that match a pattern.
    """

    import smot.algorithm as alg
    import re

    if file:
        with open(pattern, "r") as f:
            patterns = [p.strip() for p in f.readlines()]
            if invert_match:
                matcher = lambda s: not any([p in s for p in patterns])
            else:
                matcher = lambda s: any([p in s for p in patterns])
    elif perl:
        regex = re.compile(pattern)
        if invert_match:
            matcher = lambda s: not re.search(regex, s)
        else:
            matcher = lambda s: bool(re.search(regex, s))
    else:
        if invert_match:
            matcher = lambda s: pattern not in s
        else:
            matcher = lambda s: pattern in s

    def fun_(node: AnyNode) -> List[AnyNode]:
        return [
            kid for kid in node.kids if (not kid.data.isLeaf or matcher(kid.data.label))
        ]

    tree_obj = read_tree(tree)
    tree_obj.tree = alg.clean(alg.treecut(tree_obj.tree, fun_))

    if newick:
        print(sf.newick(tree_obj))
    else:
        print(sf.nexus(tree_obj))


@click.command(name="filter")
# conditions used to select groups upon which an action is performed
@click.option(
    "--all-match", multiple=True, help="Select if all tips match this expression"
)
@click.option(
    "--some-match",
    multiple=True,
    help="Select if one or more tips match this expression",
)
@click.option(
    "--none-match", multiple=True, help="Select if no tips match this expression"
)
@click.option(
    "--larger-than",
    type=int,
    help="Select if the number of tips is larger than or equal to this number",
)
@click.option(
    "--smaller-than",
    type=int,
    help="Select if the number of tips is smaller than or equal to this number",
)
# actions
@click.option("--remove", is_flag=True, help="Remove group if all conditions are met")
@click.option(
    "--color",
    type=str,
    help="Color the clade branches this color if all conditions are met",
)
@click.option(
    "--sample",
    type=float,
    help="Sample this proportion (0-1) of the group if all conditions are met",
)
@click.option(
    "--replace",
    nargs=2,
    help="Replace arg1 with arg2 in all leaf names in group if all conditions are met",
)
@factoring
@dec_default
@dec_patristic
@dec_seed
@dec_newick
@dec_tree
def filter_cmd(
    # conditions
    all_match: List[str],
    some_match: List[str],
    none_match: List[str],
    larger_than: Optional[int],
    smaller_than: Optional[int],
    # actions
    remove: bool,
    color: Optional[str],
    sample: Optional[float],
    replace: Tuple[str, str],
    # factor methods
    factor_by_capture: Optional[str],
    factor_by_field: Optional[int],
    factor_by_table: Optional[str],
    default: Optional[str],
    # phylogenetic options
    patristic: bool,
    seed: Optional[int],
    # boilerplate
    newick: bool,
    tree: TextIO,
) -> None:
    """
    Subset or modify taxa by group.

    `smot filter` performs flexible actions (remove, color, sample, or replace)
    on monophyletic groups that meet specified conditions (all-match,
    some-match, longer-than, etc).

    Examples:

      \b
      # Color any monophyletic swine branches with at least one 2021 representative red
      smot filter --factor-by-capture="(swine|human)" --all-match="swine" --some-match="2021" --color="#FF0000" pdm.tre

      \b
      # Remove any singleton swine clade
      smot filter --factor-by-capture="(swine|human)" --smaller-than=2 --remove pdm.tre

      \b
      # Downsample any monophyletic group with more than 100 members
      smot filter --factor-by-capture="(1B[^|]*)" --larger-than=10 --sample=0.1 1B.tre
    """
    import smot.algorithm as alg
    import re

    tree_obj = read_tree(tree)
    tree_obj.tree = factorTree(
        node=tree_obj.tree,
        factor_by_capture=factor_by_capture,
        factor_by_field=factor_by_field,
        factor_by_table=factor_by_table,
        default=default,
        patristic=patristic,
    )

    def condition(node: AnyNode) -> bool:
        tips = alg.tips(node)
        return (
            (not larger_than or len(tips) > larger_than)
            and (not smaller_than or len(tips) < smaller_than)
            and (
                not all_match
                or all(
                    [all([re.search(pat, tip) for tip in tips]) for pat in all_match]
                )
            )
            and (
                not some_match
                or all(
                    [any([re.search(pat, tip) for tip in tips]) for pat in some_match]
                )
            )
            and (
                not none_match
                or all(
                    [
                        all([not re.search(pat, tip) for tip in tips])
                        for pat in none_match
                    ]
                )
            )
        )

    action: Callable[[AnyNode], Optional[AnyNode]]
    if remove:

        def action(x):
            return None

    elif color is not None:
        checkColor(color)

        def action(x):
            return alg.colorTree(x, color)

    elif sample is not None:

        def action(x):
            return alg.sampleMonophyletic(
                x, proportion=sample, scale=None, minTips=3, keep_regex="", seed=seed
            )

    elif replace is not None:

        def _fun(d: AnyNodeData) -> AnyNodeData:
            d.label = re.sub(replace[0], replace[1], d.label)
            return d

        def action(x):
            return alg.treemap(x, _fun)

    else:
        # If no action is set, do nothing
        def action(x):
            return x

    filteredNode = alg.filterMono(tree_obj.tree, condition=condition, action=action)

    if filteredNode is None:
        # make an empty tree
        tree_obj.tree = makeTree(makeNode())
    else:
        # otherwise clean the existing node
        tree_obj.tree = alg.clean(filteredNode)

    if newick:
        print(sf.newick(tree_obj))
    else:
        print(sf.nexus(tree_obj))


@click.command()
@click.option(
    "-p",
    "--pattern",
    nargs=2,
    multiple=True,
    help="This option takes two arguments: 1) a pattern to match against the taxa labels and 2) the hexadecimal color that will be assigned to the taxa label. The option may be used many times.",
)
@click.option(
    "-P", "--perl", is_flag=True, help="Interpret the pattern as a regular expression"
)
@dec_tree
def leaf(pattern: List[Tuple[str, str]], perl: bool, tree: TextIO) -> None:
    """
    Color the taxa labels on a tree.

    Tips are colored based on exact or regex matches against taxon labels.
    Multiple patterns may be colored with one command by chaining `-p` options.
    The tips are colored in the order that the `-p` options are specified, so
    previously colored labels may be recolored by subsequent commands.

    The output file is always in nexus format.

    Examples:

      smot color leaf -p swine "#FFA500" -p "2020-" "#00FF00" 1B.tre

      smot color leaf --perl -p "202[012]-..-..$" "#00FF00" 1B.tre
    """
    import smot.algorithm as alg
    import re

    tree_obj = read_tree(tree)

    tips = alg.tips(tree_obj.tree)

    for (pat_str, col) in pattern:
        if perl:
            pat = re.compile(pat_str)
            matcher = lambda x: bool(re.search(pat, x))
        else:
            matcher = lambda x: pat_str in x
        for tip in tips:
            if matcher(tip):
                tree_obj.colmap[tip] = col

    print(sf.nexus(tree_obj))


colormap_arg = click.option(
    "-c",
    "--colormap",
    type=click.Path(exists=True),
    help="A TAB-delimited, headless table with columns for factor names and hexadecimal colors",
)


def chooseColorScheme(factors: List[str]) -> Dict[str, str]:
    # these colors are adapted from Paul Tol's notes here: https://personal.sron.nl/~pault/#sec:qualitative
    if len(factors) == 2:
        # orange and blue
        colors = ["#FFA000", "#0000FF"]
    elif len(factors) == 3:
        # Paul's three
        colors = ["#004488", "#DDAA33", "#BB5566"]
    elif len(factors) <= 6:
        # Paul's medium-contrast 6
        colors = ["#5486C0", "#053275", "#E9C353", "#866503", "#E7849A", "#863144"]
    elif len(factors) <= 11:
        # Paul's sunset
        colors = [
            "#2A3789",
            "#3A65A8",
            "#5C95C2",
            "#87BEDA",
            "#E5E8C0",
            "#FCD17A",
            "#FAA353",
            "#F1693C",
            "#D32623",
            "#91001C",
        ]
    else:
        die("I can't handle more than 11 colors yet")

    colormap = {f: c for (f, c) in zip(factors, colors)}

    return colormap


def colorBranches(
    is_para: bool,
    factor_by_capture: Optional[str],
    factor_by_field: Optional[int],
    factor_by_table: Optional[str],
    colormap: Optional[str],
    tree: TextIO,
):
    import smot.algorithm as alg

    tree_obj = read_tree(tree)

    tree_obj.tree = factorTree(
        node=tree_obj.tree,
        factor_by_capture=factor_by_capture,
        factor_by_field=factor_by_field,
        factor_by_table=factor_by_table,
    )
    tree_obj.tree = alg.setFactorCounts(tree_obj.tree)

    factors = sorted(list(tree_obj.tree.data.factorCount.keys()))

    _colormap = dict()
    if colormap:
        with open(colormap, "r") as f:
            try:
                _colormap = {
                    f.strip(): c.strip().upper()
                    for (f, c) in [p.strip().split("\t") for p in f.readlines()]
                }
                for clade, color in _colormap.items():
                    if color[0] != "#":
                        _colormap[clade] = "#" + color
                    if len(color) != 7:
                        die('Expected colors in hexadecimal (e.g., "#AA10FF")')
            except ValueError:
                die("Invalid color map: expected TAB-delimited, two-column file")
    else:
        _colormap = chooseColorScheme(factors)

    if is_para:
        tree_obj.tree = alg.colorPara(tree_obj.tree, colormap=_colormap)
    else:
        tree_obj.tree = alg.colorMono(tree_obj.tree, colormap=_colormap)

    print(sf.nexus(tree_obj))


@click.command(name="mono")
@factoring
@colormap_arg
@dec_tree
def mono_color_cmd(**kwargs):
    """
    Color a tree by monophyletic factor.

    For example, if we wanted to color the clades in the file 1B.tre (from
    smot/test-data in the package repo), we would need to give smot a pattern
    for extracting clade names from taxon labels. We can do this via regex
    capture as shown below, where we define a clade name as a string beginning
    with "1B." and continuing until the '|' delimiter is reached or the label
    ends:

      smot color branch mono --factor-by-capture="(1B\.[^|]*)" 1B.tre

    This will create a Nexus file with the 1B clade branches given default
    colors. If instead you want to define your own colors, you can provide a
    color map table as a two-column TAB-separated file. For example:

      \b
      1B.2.2.1 #dfc27d
      1B.2.2.2 #f6e8c3
      1B.2.1   #c7eae5

    Saving this under "1B-colors.tab", we can use these custom colors as follows:

      smot color branch mono --factor-by-capture="(1B\.[^|]*)" --colormap=1B-colors.tab 1B.tre

    Any factors/clades not included in the colormap will default to black.
    """
    colorBranches(is_para=False, **kwargs)


@click.command(name="para")
@factoring
@colormap_arg
@dec_tree
def para_color_cmd(**kwargs):
    """
    Color a tree by paraphyletic factor.

    For example, we could color the swine and human clades in the influenza
    2009 pandemic clade as follows (using a file from smot/test-data folder in
    the smot package repo):

      smot color branch para --factor-by-capture="(swine|human)" pdm.tre

    This will create a Nexus file with human and swine branches given default
    colors. If instead you want to define your own colors, you can provide a
    color map table as a two-column TAB-separated file. For example:

      \b
      human #090909
      swine #FF1000

    Saving this under "pdm-colors.tab", we can use these custom colors as follows:

      smot color branch para --factor-by-capture="(swine|human)" --colormap=pdm-colors.tab pdm.tre

    Any factors/clades not included in the colormap will default to black.
    """
    colorBranches(is_para=True, **kwargs)


@click.command(name="rm")
@click.option(
    "--newick",
    is_flag=True,
    help="Write output in newick format (metadata will be lost)",
)
@dec_tree
def rm_color(newick: bool, tree: TextIO) -> None:
    """
    Remove all color annotations from a tree
    """
    import smot.algorithm as alg

    tree_obj = read_tree(tree)
    tree_obj.colmap = dict()

    def _fun(d):
        if d.form and "!color" in d.form:
            del d.form["!color"]
        return d

    tree_obj.tree = alg.treemap(tree_obj.tree, _fun)

    if newick:
        print(sf.newick(tree_obj))
    else:
        print(sf.nexus(tree_obj))


# Remove all black color
def make_unblack(colmap: Dict[str, str]) -> Callable[[AnyNodeData], AnyNodeData]:
    def unblack(x: AnyNodeData) -> AnyNodeData:
        if "!color" in x.form and x.form["!color"] == "#000000":
            del x.form["!color"]
        if x.isLeaf and x.label in colmap and colmap[x.label] == "#000000":
            del colmap[x.label]
        return x

    return unblack


# color nodes by tip
def make_tip2node(
    colmap: Dict[str, str]
) -> Callable[[AnyNodeData, List[AnyNodeData]], AnyNodeData]:
    def tip2node(x, kids):
        child_node_colors = [
            kid.form["!color"]
            for kid in kids
            if "!color" in kid.form and kid.form["!color"]
        ]
        child_leaf_colors = [
            colmap[kid.label] for kid in kids if kid.isLeaf and kid.label in colmap
        ]
        child_colors = set(child_node_colors + child_leaf_colors)
        if len(child_colors) == 1:
            x.form["!color"] = list(child_colors)[0]
        return x

    return tip2node


# color tips by node
def make_node2tip(
    colmap: Dict[str, str]
) -> Callable[[AnyNodeData, AnyNodeData], AnyNodeData]:
    def node2tip(x, kid):
        if "!color" in x.form:
            if "!color" not in kid.form:
                kid.form["!color"] = x.form["!color"]
            if kid.isLeaf:
                colmap[kid.label] = x.form["!color"]
        return kid

    return node2tip


@click.command(name="pull")
@dec_tree
def pull_color(tree: TextIO) -> None:
    "Pull colors from tips to nodes"

    import smot.algorithm as alg

    tree_obj = read_tree(tree)

    colmap = tree_obj.colmap

    tree_obj.tree = alg.treemap(tree_obj.tree, make_unblack(colmap))
    tree_obj.tree = alg.treepull(tree_obj.tree, make_tip2node(colmap))
    tree_obj.tree = alg.treepush(tree_obj.tree, make_node2tip(colmap))

    print(sf.nexus(tree_obj))


@click.command(name="push")
@dec_tree
def push_color(tree: TextIO):
    "Push colors from nodes to tips"

    import smot.algorithm as alg

    tree_obj = read_tree(tree)

    colmap = tree_obj.colmap

    tree_obj.tree = alg.treemap(tree_obj.tree, make_unblack(colmap))
    tree_obj.tree = alg.treepush(tree_obj.tree, make_node2tip(colmap))

    print(sf.nexus(tree_obj))


CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


@click.group(
    help="Simple Manipulation Of Trees",
    context_settings=CONTEXT_SETTINGS,
    epilog=make_epilog("smot color"),
)
@click.version_option(__version__, "-v", "--version", message=__version__)
def cli():
    pass


@click.group(context_settings=CONTEXT_SETTINGS, epilog=make_epilog("smot sample para"))
def sample():
    """
    Subsample the tree. There are three subsampling algorithms: equal, mono and
    para. For details on each see the specific subcommand help statements.
    
    Each of the algorithms begins by assigning labels to the taxa. These labels
    may be extracted from the taxon names using a regular expressions
    (--factor-by-capture), the index of a field given a delimiter
    (--factor-by-field), or by looking up the taxon name in an external table
    (--factor-by-table). Some (often most) of the taxa may be unlabeled.

    Once a subset of the taxa are labeled, each algorithm will partition the
    tree into sampling groups. Taxa will then be selected from each group and
    the tree will be pruned to the selection.

    The following three examples show three ways of labeling taxa:

      \b
      smot sample mono --factor-by-field=6 -p 0.25 1B.tre
      smot sample mono --factor-by-table 1B.tab -p 0.25  1B.tre
      smot sample mono --factor-by-capture "\|(1B\.[^|]*)" -p 0.25 1B.tre

    The files 1B.tre and 1B.tab are available in the test-data/ folder in the
    smot GitHub repo.

    Taxon names have formats such as:

      CVV|A/Michigan/383/2018|H1N2|human|USA|1B.2.1|2018-07-31

    The --factor-by-field=6 option selects the 6th field (1B.2.1 in this
    case), --factor-by-table looks up the entire string in the TAB-delimited
    table 1B.tab, and --factor-by-capture regular expression finds the label
    grouped in the parentheses.
    """
    pass


sample.add_command(sample_equal_cmd)
sample.add_command(sample_mono_cmd)
sample.add_command(sample_para_cmd)


@click.group(epilog=make_epilog("smot color branch mono"))
def branch():
    """
    Color the branches of a tree. You may provide a color map; if you do not,
    smot will automatically map factors to colors from a color-blind friendly
    palette. See the mono and para help sections for examples.
    """
    pass


branch.add_command(mono_color_cmd)
branch.add_command(para_color_cmd)


@click.group(context_settings=CONTEXT_SETTINGS, epilog=make_epilog("smot color branch"))
def color():
    """
    Color the leafs or branches.

    The coloring philosophy in smot is to encode information about the specific
    taxon in the taxon label color and to encode data about groups of taxa in
    the branch color.

    If you want to color leafs by phylogenetic group, you may first color by
    branch and then push the colors to the leafs:

      smot color branch mono --factor-by-field 1 -c 1B-colors.tab 1B.tre | smot color push

    This will identify all monophyletic groups based on the clade name found in
    the first position of the taxon label (e.g., ">primate|..."). The
    monophyletic branches are colored based a color map, which should have an
    entry such as `primate #00FF00`. Then `smot color push` takes colors in nodes and
    pushes them recursively to their children, ultimately pushing the colors
    down to the taxon labels.

    Conversely, taxon label colors can be pulled up into parent nodes using
    `smot color pull`.

    Any colored branches or leafs that are not overwritten by an operation keep
    there original colors. Thus color commands can be chained together. If you
    want to start with no color, first call `smot color rm` to remove all color
    from the file.

    Smot only supports color in Nexus format.
    """
    pass


color.add_command(leaf)
color.add_command(branch)
color.add_command(rm_color)
color.add_command(push_color)
color.add_command(pull_color)

cli.add_command(tips)
cli.add_command(sample)
cli.add_command(factor)
cli.add_command(tipsed)
cli.add_command(grep)
cli.add_command(filter_cmd)
cli.add_command(color)


def main():
    sys.setrecursionlimit(1000000)
    cli()
