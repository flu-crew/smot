import parsec as p

class Node:
    def __init__(self, kids=None, label=None, form=None, length=None):
        self.kids = kids
        self.label = label
        self.form = form
        self.length = length

    def __eq__(self, other):
        return (
            self.kids == other.kids
            and self.label == other.label
            and self.form == other.form
            and self.length == other.length
        )


def p_parens(parser):
    return p.string("(") >> parser << p.string(")")


def p_brackets(parser):
    return p.string("[") >> parser << p.string("]")


def p_tuple(parser):
    return p_parens(p.sepBy1(parser, p.string(",")))


p_number = (p.regex("\d+\.\d+") ^ p.regex("\d+")).parsecmap(float)
p_label = (
    (p.string("'") >> p.regex("[^']+") << p.string("'"))
    ^ (p.string('"') >> p.regex('[^"]+') << p.string('"'))
    ^ p.regex("[^,:;()[\]]+")
)
p_length = p.string(":") >> p_number
p_format = p_brackets(p.regex("[^\]]*"))

p_term = (p_label + p.optional(p_format) + p.optional(p_length)).parsecmap(
    lambda x: (x[0][0], x[0][1], x[1])
)

p_leaf = p_term.parsecmap(lambda x: Node(kids=None, label=x[0], form=x[1], length=x[2]))
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
