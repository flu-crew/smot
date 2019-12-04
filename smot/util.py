import sys


def log(msg):
    print(msg, file=sys.stderr)


def die(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


def concat(xss):
    ys = []
    for xs in xss:
        ys + xs
    return ys


def rmNone(xs):
    return [x for x in xs if x is not None]
