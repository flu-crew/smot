#!/usr/bin/env python3

import smot.src.parser as sp
from smot.src.classes import Node
from smot.src.algorithm import *
import parsec as psc
import unittest
import random


class TestParsers(unittest.TestCase):
    def test_parens(self):
        self.assertEqual(sp.p_parens(psc.digit()).parse("(1)"), "1")

    def test_brackets(self):
        self.assertEqual(sp.p_brackets(psc.digit()).parse("[1]"), "1")

    def test_tuple(self):
        self.assertEqual(sp.p_tuple(psc.digit()).parse("(3,2,1)"), ["3", "2", "1"])
        self.assertEqual(sp.p_tuple(psc.digit()).parse("(3)"), ["3"])
        self.assertRaises(
            psc.ParseError, lambda x: sp.p_tuple(psc.digit()).parse(x), "()"
        )

    def test_number(self):
        self.assertEqual(sp.p_number.parse("12341"), 12341)
        self.assertEqual(sp.p_number.parse("-12341"), -12341)
        self.assertEqual(sp.p_number.parse("123.41"), 123.41)
        self.assertEqual(sp.p_number.parse("0.41"), 0.41)
        self.assertEqual(sp.p_number.parse("-0.41"), -0.41)
        self.assertEqual(sp.p_number.parse("1.211E2"), 121.1)
        self.assertEqual(sp.p_number.parse("1.211e2"), 121.1)
        self.assertEqual(sp.p_number.parse("1.21e-2"), 0.0121)
        self.assertEqual(sp.p_number.parse("1.21E-2"), 0.0121)
        self.assertEqual(sp.p_number.parse("-1.21E-2"), -0.0121)

    def test_label(self):
        self.assertEqual(sp.p_label.parse("'12341'"), "12341")
        self.assertEqual(
            sp.p_label.parse("'pinky pie \"!@(*&#^'"), 'pinky pie "!@(*&#^'
        )
        self.assertEqual(
            sp.p_label.parse('"pinky pie \'!@(*&#^"'), "pinky pie '!@(*&#^"
        )
        self.assertEqual(sp.p_label.parse("this/is_sparta"), "this/is_sparta")

    def test_length(self):
        self.assertEqual(sp.p_length.parse(":0.41"), 0.41)

    def test_format(self):
        self.assertEqual(sp.p_format.parse("[&!color=#000000]"), "&!color=#000000")

    def test_info(self):
        self.assertEqual(sp.p_loop.parse("[&!color=#000000]"), "&!color=#000000")

    def test_term(self):
        self.assertEqual(sp.p_term.parse("A[foo]:0.42"), ("A", "foo", 0.42))
        self.assertEqual(sp.p_term.parse("A:0.42"), ("A", None, 0.42))
        self.assertEqual(sp.p_term.parse("A[foo]"), ("A", "foo", None))
        self.assertEqual(sp.p_term.parse("A"), ("A", None, None))

    def test_info(self):
        self.assertEqual(sp.p_info.parse("A[foo]:0.42"), ("A", "foo", 0.42))
        self.assertEqual(sp.p_info.parse("A:0.42"), ("A", None, 0.42))
        self.assertEqual(sp.p_info.parse("A[foo]"), ("A", "foo", None))
        self.assertEqual(sp.p_info.parse(""), (None, None, None))

    def test_leaf(self):
        self.assertEqual(
            sp.p_leaf.parse("A[foo]:0.42"), sp.Node(label="A", form="foo", length=0.42)
        )

    def test_node(self):
        self.assertEqual(
            sp.p_node.parse("(A[foo]:0.42)Root"),
            sp.Node(kids=[sp.Node(label="A", form="foo", length=0.42)], label="Root"),
        )

    def test_newick(self):
        self.assertEqual(
            sp.p_newick.parse("(A[foo]:0.42)Root;"),
            sp.Node(kids=[sp.Node(label="A", form="foo", length=0.42)], label="Root"),
        )
        self.assertEqual(
            sp.p_newick.parse("(B,(A,C,E),D);"),
            sp.Node(
                kids=[
                    sp.Node(label="B"),
                    sp.Node(
                        kids=[
                            sp.Node(label="A"),
                            sp.Node(label="C"),
                            sp.Node(label="E"),
                        ]
                    ),
                    sp.Node(label="D"),
                ]
            ),
        )


class TestStringify(unittest.TestCase):
    def test_stringify(self):
        s = "(B|a,(A|b,C|b,E|b),D|c);"
        self.assertEqual(sp.p_newick.parse(s).newick(), s)

    def test_string_complex(self):
        s = """("that's cool"[&!color=#000000]:0.3);"""
        self.assertEqual(sp.p_newick.parse(s).newick(), s)

        s = """(A:3);"""
        self.assertEqual(sp.p_newick.parse(s).newick(), s)

        s = """('that"s !@#$%^&)(*&^[]cool'[&!color=#000000]:0.3);"""
        self.assertEqual(sp.p_newick.parse(s).newick(), s)


class TestALgorithms(unittest.TestCase):
    def test_treemap(self):
        def _lower(x):
            if x.label:
                x.label = x.label.lower()
            return x

        self.assertEqual(
            treemap(sp.p_newick.parse("(B,(A,C,E),D);"), _lower),
            sp.Node(
                kids=[
                    sp.Node(label="b"),
                    sp.Node(
                        kids=[
                            sp.Node(label="a"),
                            sp.Node(label="c"),
                            sp.Node(label="e"),
                        ]
                    ),
                    sp.Node(label="d"),
                ]
            ),
        )

    def test_treefold(self):
        def _fun(b, x):
            b.append(x.label)
            return b

        self.assertEqual(
            treefold(sp.p_newick.parse("(B,(A,C,E),D);"), _fun, []),
            [None, "B", None, "A", "C", "E", "D"],
        )

    def test_factorByLabel(self):
        def _fun(name):
            try:
                return name.split("|")[1]
            except:
                return None

        self.assertEqual(
            factorByLabel(sp.p_newick.parse("(B|a,(A|b,C|b,E|b),D|c);"), _fun),
            sp.Node(
                kids=[
                    sp.Node(label="B|a", factor="a"),
                    sp.Node(
                        kids=[
                            sp.Node(label="A|b", factor="b"),
                            sp.Node(label="C|b", factor="b"),
                            sp.Node(label="E|b", factor="b"),
                        ]
                    ),
                    sp.Node(label="D|c", factor="c"),
                ]
            ),
        )

    def test_getLeftmost(self):
        self.assertEqual(
            getLeftmost(sp.p_newick.parse("(B,(A,C,E),D);")), Node(label="B")
        )

    def test_sampleContext(self):
        self.assertEqual(
            sampleContext(
                factorByField(sp.p_newick.parse("(B|a,(A|b,C|b,E|b),D|c);"), field=2),
                keep=[],
                maxTips=1,
            ),
            sp.Node(
                kids=[
                    sp.Node(label="B|a", factor="a"),
                    sp.Node(label="A|b", factor="b"),
                    sp.Node(label="D|c", factor="c"),
                ]
            ),
        )

        self.assertEqual(
            sampleContext(
                factorByField(sp.p_newick.parse("(B|a,(A|b,C|b,E|b),D|c);"), field=2),
                keep=[],
                maxTips=2,
            ),
            sp.Node(
                kids=[
                    sp.Node(label="B|a", factor="a"),
                    sp.Node(
                        kids=[
                            sp.Node(label="A|b", factor="b"),
                            sp.Node(label="C|b", factor="b"),
                        ]
                    ),
                    sp.Node(label="D|c", factor="c"),
                ]
            ),
        )

    def test_clean(self):
        self.assertEqual(
            clean(sp.p_newick.parse("(B,((A)),D);")), sp.p_newick.parse("(B,A,D);")
        )
        self.assertEqual(
            clean(sp.p_newick.parse("(((A)));")), sp.p_newick.parse("(A);")
        )
        self.assertEqual(
            clean(sp.p_newick.parse("((((((B)),((A))))));")),
            sp.p_newick.parse("(B,A);"),
        )
        self.assertEqual(
            clean(sp.p_newick.parse("((((A,B))));")), sp.p_newick.parse("(A,B);")
        )
        self.assertEqual(
            clean(sp.p_newick.parse("(((A,B)),((((C)))));")),
            sp.p_newick.parse("((A,B),C);"),
        )
        self.assertEqual(
            clean(sp.p_newick.parse("(B:1,((A:3):2):1,D:1);")),
            sp.p_newick.parse("(B:1,A:6,D:1);"),
        )

    def test_sampleRandom(self):

        self.assertEqual(
            sampleRandom(sp.p_newick.parse("(B,(A,C,E),D);"), 5, rng=random.Random(42)),
            sp.p_newick.parse("(B,(A,C,E),D);"),
        )

        self.assertEqual(
            sampleRandom(
                sp.p_newick.parse("(B,(A,C,E),D);"), 10, rng=random.Random(42)
            ),
            sp.p_newick.parse("(B,(A,C,E),D);"),
        )
        self.assertEqual(
            sampleRandom(
                sp.p_newick.parse("(B,(A,C,E),D);"), 10, rng=random.Random(42)
            ),
            sp.p_newick.parse("(B,(A,C,E),D);"),
        )
        # this SHOULD work, but there appears to be a bug in unittest
        self.assertEqual(
            sampleRandom(sp.p_newick.parse("(B,(A,C,E),D);"), 2, rng=random.Random(42)),
            sp.p_newick.parse("(A,E);"),
        )

    def test_sampleParaphyletic(self):
        fork = sp.p_newick.parse(
            "(X1|H,(X2|H,(X3|H,(X4|H,((Y1|H,(Y2|H,(Y3|H,(Y4|H,Y5|H)))),X6|S)))));"
        )
        fork = factorByField(fork, field=2)

        self.assertEqual(
            sampleParaphyletic(fork, proportion=0.3, keep=["S"], minTips=2, seed=42),
            sp.p_newick.parse("(X1|H,(X4|H,((Y2|H,Y3|H),X6|S)));"),
        )

    def test_distribute(self):
        self.assertEqual(distribute(5, 3), [2, 2, 1])
        self.assertEqual(distribute(3, 5), [1, 1, 1, 0, 0])
        self.assertEqual(distribute(5, 1), [5])
        self.assertEqual(distribute(0, 2), [0, 0])
        self.assertEqual(distribute(5, 0), [])
        self.assertEqual(distribute(0, 0), [])
        # with sizes vector
        self.assertEqual(distribute(10, 3, [3, 100, 1]), [3, 6, 1])
        self.assertEqual(distribute(10, 3, [3, 100, 0]), [3, 7, 0])
        self.assertEqual(distribute(1, 2, [0, 10]), [0, 1])

    def test_sampleN(self):
        self.assertEqual(str(sampleN(sp.p_newick.parse("(B,(A,C,E),D);"), 2)), "(B,A)")


if __name__ == "__main__":
    unittest.main()
