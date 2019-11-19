import sys


def log(msg):
    print(msg, file=sys.stderr)


def die(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)
