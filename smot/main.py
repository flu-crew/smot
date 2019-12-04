#!/usr/bin/env python3

"""
Do stuff to trees

Usage:
    smot convert --from=<from> --to=<to> [<filename>]
    smot tips [<filename>]
    smot plot [<filename>]
    smot sample (equal|prop|para)
        [--factor-by-capture=<capture>]
        [--factor-by-field=<factorByField>]
        [--factor-by-table=<tablefile>]
        [--keep=<keep>] [--default=<defaultFactor>]
        [--max-tips=<tips>] [--min-tips=<tips>]
        [--proportion=<proportion>] [--seed=<seed>] [--zero]
        [<filename>]
    smot factor (table|prepend|append) 
        [--factor-by-field=<factorByField>]
        [--factor-by-capture=<capture>]
        [--factor-by-table=<tablefile>]
        [--default=<defaultFactor>]
        [--impute]
        [<filename>]
    smot tipsed <pattern> <replacement> [<filename>]
    smot midpoint [<filename>]
    smot random [--seed=seed] [<tipnames>]
    smot clean [<filename>]

Options
    --zero                    Set branches without lengths to 0  
    -k --keep LIST            Factors to keep
    equal                     Sampling method - equally sample from each subtree
    prop                      Sampling method - proportionally sample from tips
    para                      Sampling method - proportional sampling across branches
    -m --max-tips INT         With sample-equal, maximum number of tips to keep per unkept factor
    -m --min-tips INT         With sample-prop and sample-para, maximum number of tips to keep per unkept factor
    --factor-by-field INT     Factor by field index (with '|' delimiters, for now)
    --factor-by-capture REGEX A regular expression with a capture for determining factors from labels
    -p --proportion NUM       The proportion of tips in a clade to keep
    -d --default STR          The name to assign to tips that do not match a factor
    --impute                  Infer the factor from context, if possible
"""

import signal
import os
from docopt import docopt
from smot.version import __version__


def factorTree(tree, args, default=None):
    import smot.algorithm as alg

    if args["--factor-by-field"]:
        try:
            field = int(args["--factor-by-field"])
        except ValueError:
            die(
                f"""Expected a positive integer for field --factor-by-field, got '{args["--factor-by-field"]}'"""
            )
        tree = alg.factorByField(tree, field, default=default)
    elif args["--factor-by-capture"]:
        tree = alg.factorByCapture(
            tree, pat=args["--factor-by-capture"], default=default
        )
    elif args["--factor-by-table"]:
        tree = alg.factorByTable(
            tree, filename=args["--factor-by-table"], default=default
        )
    tree = alg.setFactorCounts(tree)
    return tree


def cast(args, field, default, lbnd=None, rbnd=None, caster=None, typename=None):
    """
    Cast a field from the command line argument list.
    """
    if args[field]:
        if caster:
            try:
                x = caster(args[field])
                if lbnd and x < lbnd:
                    print(f"Expected {field} to be greater than or equal to {lbnd}")
                if rbnd and x > rbnd:
                    print(f"Expected {field} to be less than or equal to {rbnd}")
            except ValueError:
                print(f"Expected argument {field} to be a {typename}")
                sys.exit(1)
        else:
            x = args[field]
    else:
        x = default
    return x


def main():
    if os.name is "posix":
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)

    args = docopt(__doc__, version=f"smot {__version__}")

    from smot.classes import Node
    from smot.parser import p_tree
    import smot.algorithm as alg
    import sys

    sys.setrecursionlimit(10 ** 8)

    if args["random"]:
        from Bio import Phylo
        import random

        if args["<tipnames>"]:
            with open(tipfile, "r") as f:
                names = [name.strip() for name in f.readlines()]
        else:
            names = [name.strip() for name in sys.stdin]
        seed = cast(args, "--seed", None, caster=int, typename="int", lbnd=0)
        random.seed(seed)
        btree = Phylo.BaseTree.Tree.randomized(names)
        Phylo.write(btree, file=sys.stdout, format="newick")
        sys.exit(0)

    if args["convert"]:
        from Bio import Phylo

        Phylo.convert(args["<filename>"], args["--from"], sys.stdout, args["--to"])
        sys.exit(1)

    if args["<filename>"]:
        f = open(args["<filename>"], "r")
    else:
        f = sys.stdin

    rawtree = f.readlines()
    rawtree = "\n".join(rawtree).strip()
    tree = p_tree.parse(rawtree)

    if args["midpoint"]:
        from Bio import Phylo

        btree = Phylo.BaseTree.Tree.from_clade(tree.asBiopythonTree())
        btree.root_at_midpoint()
        Phylo.write(btree.clade, file=sys.stdout, format="newick")
        sys.exit(0)
    elif args["plot"]:
        from Bio import Phylo

        btree = Phylo.BaseTree.Tree.from_clade(tree.asBiopythonTree())
        btree.ladderize(reverse=True)
        Phylo.draw(btree)
        sys.exit(0)

    if args["tipsed"]:
        import re

        pat = re.compile(args["<pattern>"])

        def fun_(nodeData):
            if nodeData.label:
                nodeData.label = re.sub(pat, args["<replacement>"], nodeData.label)
            return nodeData

        tree = alg.treemap(tree, fun_)
        print(tree.newick())
    elif args["clean"]:
        from Bio import Phylo

        tree = alg.clean(tree)
        btree = Phylo.BaseTree.Tree.from_clade(tree.asBiopythonTree())
        btree.ladderize(reverse=True)
        Phylo.write(btree, file=sys.stdout, format="newick")
    elif args["tips"]:
        tree = alg.setNLeafs(tree)

        def _fun(b, x):
            if x.isLeaf:
                b.append(x.label)
            return b

        for tip in alg.treefold(tree, _fun, []):
            print(tip)
    elif args["factor"]:

        defaultFactor = cast(args, "--default", None)
        tree = factorTree(tree, args, default=defaultFactor)
        if args["--impute"]:
            tree = alg.imputeFactors(tree)

        if args["table"]:

            def _fun(b, x):
                if x.isLeaf:
                    if x.factor is None:
                        factor = defaultFactor
                    else:
                        factor = x.factor
                    b.append(f"{x.label}\t{factor}")
                return b

            for row in alg.treefold(tree, _fun, []):
                print(row)
            sys.exit(0)

        def _fun(x):
            if x.isLeaf:
                if x.factor is None:
                    x.factor = defaultFactor
                if args["prepend"]:
                    x.label = f"{x.factor}|{x.label}"
                else:
                    x.label = f"{x.label}|{x.factor}"
            return x

        tree = alg.treemap(tree, _fun)
        print(tree.newick())
        sys.exit(0)

    elif args["sample"]:
        tree = factorTree(tree, args, default=cast(args, "--default", None))
        keep = cast(
            args,
            "--keep",
            [],
            caster=lambda x: x.split(","),
            typename="comma separated list",
        )
        maxTips = cast(args, "--max-tips", 5, caster=int, typename="int", lbnd=0)
        if args["equal"]:
            tree = alg.sampleContext(tree, keep=keep, maxTips=maxTips)
            print(tree.newick())
            sys.exit(0)

        proportion = cast(
            args, "--proportion", 0.5, caster=float, typename="float", lbnd=0, rbnd=1
        )
        minTips = cast(args, "--min-tips", 3, caster=int, typename="int", lbnd=0)
        seed = cast(args, "--seed", None, caster=int, typename="int", lbnd=0)

        if args["prop"]:
            tree = alg.sampleProportional(
                tree, keep=keep, proportion=proportion, minTips=minTips, seed=seed
            )
        elif args["para"]:
            tree = alg.sampleParaphyletic(
                tree, keep=keep, proportion=proportion, minTips=minTips, seed=seed
            )
        print(tree.newick())
        sys.exit(0)
    else:
        print(tree.newick())


if __name__ == "__main__":
    main()
