#!/usr/bin/env python3

"""
Do stuff to trees

Usage:
    smot tips [--format=<format>] [<filename>]
    smot plot [--format=<format>] [<filename>]
    smot sample-equal [--format=<format>]
                      [--factor-by-field=<factorByField>]
                      [--factor-by-capture=<capture>]
                      [--factor-by-table=<tablefile>]
                      [--keep=<keep>] [--max-tips=<tips>] [--zero] [<filename>]
    smot sample-proportional [--format=<format>]
                             [--factor-by-field=<factorByField>]
                             [--factor-by-capture=<capture>]
                             [--factor-by-table=<tablefile>]
                             [--paraphyletic]
                             [--proportion=<proportion>] [--keep=<keep>] [--seed=<seed>]
                             [--min-tips=<tips>] [--zero] [<filename>]
    smot tipsed [--format=<format>] <pattern> <replacement> [<filename>]
    smot midpoint [--format=<format>] [<filename>]
    smot random [--format=<format>] [<tipnames>]
    smot clean [<filename>]

Options
    --zero                    Set branches without lengths to 0  
    -f --format STR           Tree format (newick or nexus)
    -k --keep LIST            Factors to keep
    -m --max-tips INT         Maximum number of tips to keep per unkept factor
    --factor-by-field INT     Factor by field index (with '|' delimiters, for now)
    --factor-by-capture REGEX A regular expression with a capture for determining factors from labels
    -p --proportion NUM       The proportion of tips in a clade to keep
    --paraphyletic            Sample across branches
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
    from smot.parser import p_newick
    import smot.algorithm as alg
    import sys

    sys.setrecursionlimit(10 ** 8)

    format = cast(args, "--format", "newick")

    if args["random"]:
        from Bio import Phylo

        if args["<tipnames>"]:
            with open(tipfile, "r") as f:
                names = [name.strip() for name in f.readlines()]
        else:
            names = [name.strip() for name in sys.stdin]
        btree = Phylo.BaseTree.Tree.randomized(names)
        Phylo.write(btree, file=sys.stdout, format="newick")
        sys.exit(0)

    if args["<filename>"]:
        f = open(args["<filename>"], "r")
    else:
        f = sys.stdin

    if args["midpoint"]:
        from Bio import Phylo

        tree = list(Phylo.parse(f, format=format))[0]
        tree.root_at_midpoint()
        Phylo.write(tree.clade, file=sys.stdout, format="newick")
        sys.exit(0)
    elif args["plot"]:
        from Bio import Phylo

        btree = list(Phylo.parse(f, format=format))[0]
        Phylo.draw(btree)
        sys.exit(0)

    rawtree = f.readlines()
    rawtree = "".join(rawtree).strip()
    tree = p_newick.parse(rawtree)

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
        tree = alg.clean(tree)
        print(tree.newick())
    elif args["tips"]:
        tree = alg.setNLeafs(tree)

        def _fun(b, x):
            if x.isLeaf:
                b.append(x.label)
            return b

        for tip in alg.treefold(tree, _fun, []):
            print(tip)
    elif args["sample-equal"] or args["sample-proportional"]:
        tree = factorTree(tree, args)
        keep = cast(
            args,
            "--keep",
            [],
            caster=lambda x: x.split(","),
            typename="comma separated list",
        )
        minTips = cast(args, "--min-tips", 3, caster=int, typename="int", lbnd=0)
        maxTips = cast(args, "--max-tips", 5, caster=int, typename="int", lbnd=0)
        seed = cast(args, "--seed", None, caster=int, typename="int", lbnd=0)
        proportion = cast(
            args, "--proportion", 0.5, caster=float, typename="float", lbnd=0, rbnd=1
        )
        if args["sample-equal"]:
            tree = alg.sampleContext(tree, keep=keep, maxTips=maxTips)
        elif args["sample-proportional"] and not args["--paraphyletic"]:
            tree = alg.sampleProportional(
                tree, keep=keep, proportion=proportion, minTips=minTips, seed=seed
            )
        elif args["sample-proportional"] and args["--paraphyletic"]:
            tree = alg.sampleParaphyletic(
                tree, keep=keep, proportion=proportion, minTips=minTips, seed=seed
            )
        print(tree.newick())
    else:
        print(tree.newick())


if __name__ == "__main__":
    main()
