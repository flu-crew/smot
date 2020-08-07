from smot.version import __version__
import click
import os
import signal
import sys

INT_SENTINEL=9999

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
                "expected a string, got "
                f"{value!r} of type {type(value).__name__}",
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
                "expected a int, got "
                f"{value!r} of type {type(value).__name__}",
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

ListOfStrings = ListOfStringsType()


def factorTree(tree, factor_by_field, factor_by_capture, factor_by_table, default=None):
    import smot.algorithm as alg

    if factor_by_field is not None:
        try:
            field = int(factor_by_field)
        except ValueError:
            die(
                f"""Expected a positive integer for field --factor-by-field, got '{factor_by_field}'"""
            )
        tree = alg.factorByField(tree, field, default=default)
    elif factor_by_capture is not None:
        tree = alg.factorByCapture(tree, pat=factor_by_capture, default=default)
    elif factor_by_table is not None:
        tree = alg.factorByTable(tree, filename=factor_by_table, default=default)
    tree = alg.setFactorCounts(tree)
    return tree


def read_tree(treefile):
    from smot.parser import p_tree

    if treefile:
        f = treefile
    else:
        f = sys.stdin

    rawtree = f.readlines()
    rawtree = "\n".join(rawtree).strip()
    tree = p_tree.parse(rawtree)
    return tree


#      smot convert --from=<from> --to=<to> [<filename>]
@click.command(help="Convert between tree formats.")
@click.option("--from", "opt_from", type=str, help="input tree format")
@click.option("--to", "opt_to", type=str, help="output tree format")
@click.argument("TREE", type=click.File())
def convert(opt_from, opt_to, tree):
    from Bio import Phylo
    Phylo.convert(tree, opt_from, sys.stdout, opt_to)


#      smot tips [<filename>]
@click.command(help="Print the tree tip labels")
@click.argument("TREE", type=click.File())
def tips(tree):
    import smot.algorithm as alg

    tree = read_tree(tree)
    tree = alg.setNLeafs(tree)

    def _fun(b, x):
        if x.isLeaf:
            b.append(x.label)
        return b

    for tip in alg.treefold(tree, _fun, []):
        print(tip)


#      smot plot [<filename>]
@click.command(help="Build a simple tree plot")
@click.argument("TREE", type=click.File())
def plot(tree):
    from Bio import Phylo
    tree = read_tree(tree)
    btree = Phylo.BaseTree.Tree.from_clade(tree.asBiopythonTree())
    btree.ladderize(reverse=True)
    Phylo.draw(btree)


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
      "--factor-by-table", type=MaybeString, help="I don't even know what this is"
  )(function)

  return(function)



dec_proportion = click.option(
    "-p",
    "--proportion",
    type=click.FloatRange(min=0, max=1),
    help="The proportion of tips in a clade to keep",
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

dec_keep = click.option("-k", "--keep", default=[], type=ListOfStrings, help="Factors to keep")

@click.command(
    help="Equal sampling. Descend from root to tip. At each node, determine if each subtree contains a single factor. If a subtree is not monophyletic, recurse into the subtree. If the subtree is monophyletic, then select up to N tips (from the --max-tips argument) from the subtree. The selection of tips is deterministic but dependent on the ordering of leaves. To sample a subtree, an equal number of tips is sampled from each descendent subtree, and so on recursively down to the tips. The resulting downsampled subtree captures the depth of the tree, but is not representative of the tree's breadth. That is, if N=6 and a tree splits into two subtrees, one with 3 tips and one with 300 tips, still 3 tips will be sampled from each branch."
)
@factoring
@dec_keep
@click.option(
    "--default", type=str, help="The name to assign to tips that do not match a factor"
)
@dec_max_tips
@click.option("--zero", is_flag=True, help="Set branches without lengths to 0")
@click.argument("TREE", type=click.File())
def equal(
    factor_by_capture,
    factor_by_field,
    factor_by_table,
    keep,
    default,
    max_tips,
    zero,
    tree,
):
    import smot.algorithm as alg
    tree = read_tree(tree)
    tree = factorTree(
        tree=tree,
        factor_by_field=factor_by_field,
        factor_by_capture=factor_by_capture,
        factor_by_table=factor_by_table,
        default=default,
    )
    tree = alg.sampleContext(tree, keep=keep, maxTips=max_tips)
    print(tree.newick())


@click.command(
    help="Proportional sampling. Randomly sample p (0 to 1, from --proportion) tips from each monophyletic (relative to factors) subtree. Retain at least N tips in each branch (--min-tips)."
)
@factoring
@dec_keep
@click.option(
    "--default", type=str, help="The name to assign to tips that do not match a factor"
)
@dec_min_tips
@dec_proportion
@dec_seed
@click.option("--zero", is_flag=True, help="Set branches without lengths to 0")
@click.argument("TREE", type=click.File())
def prop(
    factor_by_capture,
    factor_by_field,
    factor_by_table,
    keep,
    default,
    min_tips,
    proportion,
    seed,
    zero,
    tree,
):
    import smot.algorithm as alg

    tree = read_tree(tree)
    tree = factorTree(
        tree=tree,
        factor_by_field=factor_by_field,
        factor_by_capture=factor_by_capture,
        factor_by_table=factor_by_table,
        default=default,
    )
    tree = alg.sampleProportional(
        tree, keep=keep, proportion=proportion, minTips=min_tips, seed=seed
    )
    print(tree.newick())


@click.command(
    help="Paraphyletic sampling. The sampling algorithm starts at the root and descends to the tips. At each node, we store monophyletic subtrees in a list and descend into polyphyletic ones (whose leaves have multiple factors). If we reach a tip or encounter a monophyletic child of a different factor than the stored subtrees, then we stop and sample from all tips in the stored trees and initialize a new list with the new monophyletic child."
)
@factoring
@dec_keep
@click.option(
    "--default", type=str, help="The name to assign to tips that do not match a factor"
)
@dec_min_tips
@dec_proportion
@dec_seed
@click.option("--zero", is_flag=True, help="Set branches without lengths to 0")
@click.argument("TREE", type=click.File())
def para(
    factor_by_capture,
    factor_by_field,
    factor_by_table,
    keep,
    default,
    min_tips,
    proportion,
    seed,
    zero,
    tree,
):
    import smot.algorithm as alg

    tree = read_tree(tree)
    tree = factorTree(
        tree=tree,
        factor_by_field=factor_by_field,
        factor_by_capture=factor_by_capture,
        factor_by_table=factor_by_table,
        default=default,
    )
    tree = alg.sampleParaphyletic(
        tree, keep=keep, proportion=proportion, minTips=min_tips, seed=seed
    )
    print(tree.newick())


@click.command(
    help="Impute, annotate with, and/or tabulate factors. The --impute option will fill in missing factors in monophyletic branches. This is useful, for example, for inferring clades given a few references in a tree. There are three modes: 'table' prints a TAB-delimited table of tip names and factors, 'prepend' adds the factor to the beginning of the tiplabel (delimited with '|'), 'append' adds it to the end."
)
@click.argument(
    "method", type=click.Choice(["table", "prepend", "append"], case_sensitive=False)
)
@factoring
@click.option(
    "--default", type=str, default=None, help="The name to assign to tips that do not match a factor"
)
@click.option("--impute", is_flag=True, default=False, help="Infer the factor from context, if possible")
@click.argument("TREE", type=click.File())
def factor(
    method, factor_by_capture, factor_by_field, factor_by_table, default, impute, tree
):
    import smot.algorithm as alg

    tree = read_tree(tree)
    tree = factorTree(
        tree=tree,
        factor_by_field=factor_by_field,
        factor_by_capture=factor_by_capture,
        factor_by_table=factor_by_table,
        default=default,
    )

    if impute:
        tree = alg.imputeFactors(tree)

    # create TAB-delimited, table with columns for the tip labels and the
    # (possibly imputed) factor
    if method.lower() == "table":

        def _fun(b, x):
            if x.isLeaf:
                if x.factor is None:
                    factor = default
                else:
                    factor = x.factor
                b.append(f"{x.label}\t{factor}")
            return b

        for row in alg.treefold(tree, _fun, []):
            print(row)

    # prepend or append the factor to the tip labels and print the resulting tree
    else:

        def _fun(x):
            if x.isLeaf:
                if x.factor is None:
                    x.factor = default
                if method.lower() == "prepend":
                    x.label = f"{x.factor}|{x.label}"
                else:
                    x.label = f"{x.label}|{x.factor}"
            return x

        tree = alg.treemap(tree, _fun)
        print(tree.newick())


#      smot tipsed <pattern> <replacement> [<filename>]
@click.command(help="Search and replace patterns in tip labels")
@click.argument("PATTERN", type=str)
@click.argument("REPLACEMENT", type=str)
@click.argument("TREE", type=click.File())
def tipsed(pattern, replacement, tree):
    import smot.algorithm as alg
    import re

    pat = re.compile(pattern)

    def fun_(nodeData):
        if nodeData.label:
            nodeData.label = re.sub(pat, replacement, nodeData.label)
        return nodeData

    tree = read_tree(tree)
    tree = alg.treemap(tree, fun_)
    print(tree.newick())


#      smot midpoint [<filename>]
@click.command(help="Root a tree at the midpoint (disgustingly slow)")
@click.argument("TREE", type=click.File())
def midpoint(tree):
    from Bio import Phylo

    tree = read_tree(tree)
    btree = Phylo.BaseTree.Tree.from_clade(tree.asBiopythonTree())
    btree.root_at_midpoint()
    Phylo.write(btree.clade, file=sys.stdout, format="newick")


@click.command(help="Generate a random tree from a file of labels")
@dec_seed
@click.argument("tipnames", type=click.File())
def random(seed, tipnames):
    from Bio import Phylo
    import random

    if tipnames:
        names = [name.strip() for name in tipnames.readlines()]
    else:
        names = [name.strip() for name in sys.stdin]
    random.seed(seed)
    btree = Phylo.BaseTree.Tree.randomized(names)
    Phylo.write(btree, file=sys.stdout, format="newick")


#      smot clean [<filename>]
@click.command(
    help="Clean and sort the tree. Nodes with single children are removed. Branch lengths are added (defaulting to 0). The tree is sorted (the topology is NOT changed and no root is added)."
)
@click.argument("TREE", type=click.File())
def clean(tree):
    from Bio import Phylo
    import smot.algorithm as alg

    tree = read_tree(tree)
    tree = alg.clean(tree)
    btree = Phylo.BaseTree.Tree.from_clade(tree.asBiopythonTree())
    btree.ladderize(reverse=True)
    Phylo.write(btree, file=sys.stdout, format="newick")


CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


@click.group(help="Simple Manipulation Of Trees", context_settings=CONTEXT_SETTINGS)
def cli():
    pass


@click.group(
    help="Subsample the tree using various methods. The details of the sampling algorithms differ, but they all start by adding 0 or 1 labels (or factors) to each tip in the tree. These factors are assigned in 1 of 3 ways, described in the --factor-by-capture, --factor-by-field, and --factor-by-table options. Once the factors have been determined, we ascend from tip to root recording the set of all descendent factors in each node. Thus the ancestral node of a monophyletic subtree, where all leaves have the same factor (or no factor), will store a set of exactly one factor. The resulting factored tree is the starting data structure for each of the sampling algorithms.",
    context_settings=CONTEXT_SETTINGS,
)
def sample():
    pass


sample.add_command(equal)
sample.add_command(prop)
sample.add_command(para)

cli.add_command(convert)
cli.add_command(tips)
cli.add_command(plot)
cli.add_command(sample)
cli.add_command(factor)
cli.add_command(tipsed)
cli.add_command(midpoint)
cli.add_command(random)
cli.add_command(clean)


def main():
    sys.setrecursionlimit(1000000)
    cli()


if __name__ == "__main__":
    if os.name is "posix":
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    main()
