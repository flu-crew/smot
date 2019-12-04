import parsec as p
import re
from smot.util import concat, rmNone, die
from smot.classes import Node


def p_parens(parser):
    return p.string("(") >> parser << p.string(")")


def p_brackets(parser):
    return p.string("[") >> parser << p.string("]")


def p_dquoted(parser):
    return p.string('"') >> parser << p.string('"')


def p_squoted(parser):
    return p.string("'") >> parser << p.string("'")


def p_tuple(parser):
    return p_parens(p.sepBy1(parser, p.string(",")))


p_number = (
    p.regex("-?\d\.?\d*[eE]-?\d+") ^ p.regex("-?\d+\.\d+") ^ p.regex("-?\d+")
).parsecmap(float)
p_label = (
    p_squoted(p.regex("[^']+")) ^ p_dquoted(p.regex('[^"]+')) ^ p.regex("[^,:;()[\]]+")
)
p_length = p.string(":") >> p_number
p_format = p_brackets(p.regex("[^\]]*"))

p_term = (p_label + p.optional(p_format) + p.optional(p_length)).parsecmap(
    lambda x: (x[0][0], x[0][1], x[1])
)

p_leaf = p_term.parsecmap(lambda x: Node(kids=[], label=x[0], form=x[1], length=x[2]))
p_info = (p.optional(p_label) + p.optional(p_format) + p.optional(p_length)).parsecmap(
    lambda x: (x[0][0], x[0][1], x[1])
)


@p.generate
def p_node():
    r = yield (p_tuple(p_leaf ^ p_node) + p.optional(p_info)).parsecmap(
        lambda x: Node(kids=x[0], label=x[1][0], form=x[1][1], length=x[1][2])
    )
    return r


p_newick = p_node << p.string(";")


def dieIfMultiple(xs):
    if len(xs) == 1:
        return xs[0]
    else:
        die(f"Expected a single entry in this NEXUS file, found {len(xs)}")


p_boring_line = p.regex("[^\n]*\n").parsecmap(lambda x: None)

p_nexus_line = (
    p.regex("\s*tree\s+[^=]+=[^(]*", re.I) >> p_newick << p.string("\n")
) ^ p_boring_line

p_nexus = p.string("#NEXUS") >> p.many(p_nexus_line).parsecmap(rmNone).parsecmap(
    dieIfMultiple
)

p_tree = p_nexus ^ p_newick
