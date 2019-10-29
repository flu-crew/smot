#!/usr/bin/env python3

import sap as ft
import parsec as psc
import unittest


class TestParsers(unittest.TestCase):
    def test_parens(self):
        self.assertEqual(ft.p_parens(psc.digit()).parse("(1)"), "1")

    def test_brackets(self):
        self.assertEqual(ft.p_brackets(psc.digit()).parse("[1]"), "1")

    def test_tuple(self):
        self.assertEqual(ft.p_tuple(psc.digit()).parse("(3,2,1)"), ["3", "2", "1"])
        self.assertEqual(ft.p_tuple(psc.digit()).parse("(3)"), ["3"])
        self.assertRaises(
            psc.ParseError, lambda x: ft.p_tuple(psc.digit()).parse(x), "()"
        )

    def test_number(self):
        self.assertEqual(ft.p_number.parse("12341"), 12341)
        self.assertEqual(ft.p_number.parse("123.41"), 123.41)
        self.assertEqual(ft.p_number.parse("0.41"), 0.41)

    def test_label(self):
        self.assertEqual(ft.p_label.parse("'12341'"), "12341")
        self.assertEqual(
            ft.p_label.parse("'pinky pie \"!@(*&#^'"), 'pinky pie "!@(*&#^'
        )
        self.assertEqual(
            ft.p_label.parse('"pinky pie \'!@(*&#^"'), "pinky pie '!@(*&#^"
        )
        self.assertEqual(ft.p_label.parse("this/is_sparta"), "this/is_sparta")

    def test_length(self):
        self.assertEqual(ft.p_length.parse(":0.41"), 0.41)

    def test_format(self):
        self.assertEqual(ft.p_format.parse("[&!color=#000000]"), "&!color=#000000")

    def test_info(self):
        self.assertEqual(ft.p_loop.parse("[&!color=#000000]"), "&!color=#000000")

    def test_term(self):
        self.assertEqual(ft.p_term.parse("A[foo]:0.42"), ("A", "foo", 0.42))
        self.assertEqual(ft.p_term.parse("A:0.42"), ("A", None, 0.42))
        self.assertEqual(ft.p_term.parse("A[foo]"), ("A", "foo", None))
        self.assertEqual(ft.p_term.parse("A"), ("A", None, None))

    def test_info(self):
        self.assertEqual(ft.p_info.parse("A[foo]:0.42"), ("A", "foo", 0.42))
        self.assertEqual(ft.p_info.parse("A:0.42"), ("A", None, 0.42))
        self.assertEqual(ft.p_info.parse("A[foo]"), ("A", "foo", None))
        self.assertEqual(ft.p_info.parse(""), (None, None, None))

    def test_leaf(self):
        self.assertEqual(
            ft.p_leaf.parse("A[foo]:0.42"), ft.Node(label="A", form="foo", length=0.42)
        )

    def test_node(self):
        self.assertEqual(
            ft.p_node.parse("(A[foo]:0.42)Root"),
            ft.Node(kids=[ft.Node(label="A", form="foo", length=0.42)], label="Root"),
        )

    def test_newick(self):
        self.assertEqual(
            ft.p_newick.parse("(A[foo]:0.42)Root;"),
            ft.Node(kids=[ft.Node(label="A", form="foo", length=0.42)], label="Root"),
        )
        self.assertEqual(
            ft.p_newick.parse("(B,(A,C,E),D);"),
            ft.Node(
                kids=[
                    ft.Node(label="B"),
                    ft.Node(
                        kids=[
                            ft.Node(label="A"),
                            ft.Node(label="C"),
                            ft.Node(label="E"),
                        ]
                    ),
                    ft.Node(label="D"),
                ]
            ),
        )

if __name__ == "__main__":
    unittest.main()
