#!/usr/bin/env python3

"""
Do stuff to trees

Usage:
    sap tips [--format=<format>] [<filename>]
    sap plot [--format=<format>] [<filename>]
    sap sample-equal [--format=<format>] [--keep=<keep>] [--factor-by-field=<factorByField>] [--factor-by-capture=<capture>] [--max-tips=<tips>] [--zero] [<filename>]
    sap tipsed [--format=<format>] <pattern> <replacement> [<filename>]
    sap midpoint [--format=<format>] [<filename>]
    sap random [--format=<format>] [<tipnames>]

Options
    --zero                    Set branches without lengths to 0  
    -f --format STR           Tree format (newick or nexus)
    -k --keep LIST            Factors to keep
    -m --max-tips INT         Maximum number of tips to keep per unkept factor
    --factor-by-field INT     Factor by field index (with '|' delimiters, for now)
    --factor-by-capture REGEX A regular expression with a capture for determining factors from labels
"""

import signal
import os
from docopt import docopt

if __name__ == "__main__":

    if os.name is "posix":
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)

    args = docopt(__doc__, version ="sap 0.1.0")

    from src.classes import Node
    from src.parser import p_newick
    from src.algorithm import *
    import sys

    sys.setrecursionlimit(10**8)

    if args["--format"]:
        format = args["--format"]
    else:
        format = "newick"

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
        tree = treemap(tree, fun_)
        print(tree.newick())
    elif args["tips"]:
        tree = setNLeafs(tree)
        def _fun(b, x):
            if x.isLeaf:
                b.append(x.label)
            return b
        for tip in treefold(tree, _fun, []):
            print(tip)
    elif args["sample-equal"]:
        if args["--factor-by-field"]:
            def _fun(name):
                try:
                    return name.split("|")[int(args["--factor-by-field"])+1]
                except:
                    return None
            tree = factorByLabel(tree, _fun)
        elif args["--factor-by-capture"]:
            import re
            pat = re.compile(args["--factor-by-capture"])
            def _fun(name):
                if name:
                    m = re.search(pat, name)
                    if m:
                        if m.groups(1):
                            return m.groups(1)
                        else:
                            return m.groups(0)
                return "Other"
            tree = factorByLabel(tree, _fun)
        if args["--max-tips"]:
            try:
                maxTips = int(args["--max-tips"])
            except:
                print("Expected argument --max-tips to be a positive integer")
        else:
            maxTips = 5
        if args["--keep"]:
            keep = [args["--keep"]]
        else:
            keep = []
        tree = sampleContext(tree, keep=keep, maxTips=maxTips)
        print(tree.newick())
    else:
        print(tree.newick())
