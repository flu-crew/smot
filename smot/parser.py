import parsec as p
import re
from smot.util import concat, rmNone, die
from smot.classes import Node, Tree

p_whitespace = p.regex(r"\s*", re.MULTILINE)


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


p_dchar = p.many((p.string("\\") >> p.regex(".")) ^ p.none_of('"')).parsecmap(
    lambda xs: "".join(xs)
)
p_schar = p.many((p.string("\\") >> p.regex(".")) ^ p.none_of("'")).parsecmap(
    lambda xs: "".join(xs)
)

# match normal single quoted expressions
# support figtree convention of replacing within-string apostrophes with ''
p_figtree_quote = p.many1(p_squoted(p_schar)).parsecmap(lambda xs: "'".join(xs))

p_number = (
    p.regex("-?\d\.?\d*[eE]-?\d+") ^ p.regex("-?\d+\.\d+") ^ p.regex("-?\d+")
).parsecmap(float)
p_label = p_figtree_quote ^ p_dquoted(p_dchar) ^ p.regex("[^,:;()[\]]+")
p_length = p.string(":") >> p_number


def toDict(xs):
    return {k: v for (k, v) in xs}


p_keypair = (p.regex("[^=]+") << p.string("=")) + p_label
p_format = p_brackets(
    p.optional(p.string("&")) >> p.sepBy1(p_keypair, p.string(","))
).parsecmap(toDict)
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


@p.generate
def p_nexus():
    yield p.string("#NEXUS\n")
    sections = yield p.many1(p_nexus_section)
    tree = None
    colmap = dict()
    meta = dict()
    for (k, v) in sections:
        if k == "trees":
            tree = v
        elif k == "taxa":
            colmap = v
        else:
            meta[k] = v
    return Tree(tree=tree, colmap=colmap, meta=meta)


@p.generate
def p_nexus_section():
    tag = yield (
        p.regex("begin\s+") >> p.regex("[^; ]*", re.I) << p.regex("\s*;\s*\n")
    ).parsecmap(lambda x: x.lower())
    if tag == "trees":
        val = yield p.many1(p_nexus_tree_line).parsecmap(dieIfMultiple)
    # The only thing I currently use the taxalist for is to extract colors. It
    # can also be used as a map from integer indices in the newick to field
    # names, but this is not yet something I want to support.
    elif tag == "taxa":
        val = yield p_taxa_block
    else:
        val = yield p.many(p.string("\t") >> p.regex("[^;]*") << p.string(";\n"))
    yield p.regex("end;", re.I)
    yield p_whitespace
    return (tag, val)


@p.generate
def p_taxa_block():
    yield p.regex("\tdimensions.*\n", re.I)
    yield p.regex("\ttaxlabels\n", re.I)
    yield p_whitespace
    vals = yield p.many1((p_label + p.optional(p_format)) << p_whitespace)
    yield p.string(";")
    yield p_whitespace
    return make_tip_color_map(vals)


@p.generate
def p_nexus_tree_line():
    yield p.regex("\t\s*tree\s*[^ ]+\s*=[^(]*", re.I)
    tree = yield p_newick << p.string("\n")
    return tree


def make_tip_color_map(xs):
    color_map = dict()
    for (name, form) in xs:
        if not form is None and "!color" in form:
            color_map[name] = form["!color"]
    return color_map


p_newick = p_node << p.string(";")


def dieIfMultiple(xs):
    if len(xs) == 1:
        return xs[0]
    elif len(xs) == 0:
        die(
            f"Failed to parse tree. The tree may be in an unsupported format (only Nexus and Newick are supported) or the tip labels may have strange characters or escape conventions. If you are sure this is a valid tree, send it to the maintainer and ask them to fix the smot parser."
        )
    else:
        die(f"Expected a single entry in this NEXUS file, found {len(xs)}")


p_tree = p_nexus ^ p_newick.parsecmap(Tree)
