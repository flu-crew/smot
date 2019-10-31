#!/usr/bin/env python3

"""
Do stuff to trees

Usage:
    sap <filename>
    sap tips [<filename>]
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
    import sys

    sys.setrecursionlimit(10**8)

    if args["<filename>"]:
        with open(args["<filename>"], "r") as f: 
            rawtree = f.readlines()
    else:
        rawtree = sys.stdin.readlines()

    rawtree = "".join(rawtree).strip()

    tree = p_newick.parse(rawtree)
        
    print(tree.newick())
