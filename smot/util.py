from __future__ import annotations
from typing import List, TypeVar, Optional

import sys

A = TypeVar("A")


def log(msg: str) -> None:
    print(msg, file=sys.stderr)


def die(msg: str) -> None:
    print(msg, file=sys.stderr)
    sys.exit(1)


def concat(xss: List[List[A]]) -> List[A]:
    ys: List[A]
    ys = []
    for xs in xss:
        ys + xs
    return ys


def rmNone(xs: List[Optional[A]]) -> List[A]:
    return [x for x in xs if x is not None]
