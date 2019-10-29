#!/usr/bin/env python3

import src.parser as sp
from src.classes import Node
from src.algorithm import treemap, treefold, factorByLabel, sampleContext, getLeftmost
import parsec as psc
import unittest


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
        self.assertEqual(sp.p_number.parse("123.41"), 123.41)
        self.assertEqual(sp.p_number.parse("0.41"), 0.41)

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
            getLeftmost(sp.p_newick.parse("(B,(A,C,E),D);")),
            Node(label="B"),
        )

    def test_sampleContext(self):
        def _fun(name):
            try:
                return name.split("|")[1]
            except:
                return None

        self.assertEqual(
            sampleContext(factorByLabel(sp.p_newick.parse("(B|a,(A|b,C|b,E|b),D|c);"), _fun), keep=[], maxTips=2),
            sp.Node(
                kids=[
                    sp.Node(label="B|a", factor="a"),
                    sp.Node(label="A|b", factor="b"),
                    sp.Node(label="D|c", factor="c"),
                ]
            ),
        )


if __name__ == "__main__":
    unittest.main()
