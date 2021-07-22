#!/usr/bin/env python3

import smot.parser as sp
from smot.classes import Node
import smot.algorithm as alg
import parsec as psc
import unittest
import random
from smot.format import newick

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
        self.assertEqual(sp.p_label.parse("pinky pie's pink"), "pinky pie's pink")
        self.assertEqual(sp.p_label.parse("this/is_sparta"), "this/is_sparta")
        # support unicode characters
        self.assertEqual(sp.p_label.parse("'小指派'"), "小指派")
        self.assertEqual(sp.p_label.parse("😀"), "😀")

        # handle FigTree's funky escape convention
        self.assertEqual(sp.p_label.parse("''''"), "'")
        self.assertEqual(sp.p_label.parse("''''''"), "''")
        self.assertEqual(sp.p_label.parse("'''a'"), "'a")
        self.assertEqual(sp.p_label.parse("'a'''"), "a'")
        self.assertEqual(sp.p_label.parse("'''a''b''c'''"), "'a'b'c'")
        # support conventional escaping
        self.assertEqual(sp.p_label.parse("'a\\'b'"), "a'b")
        self.assertEqual(sp.p_label.parse("'a\\\\b'"), "a\\b")

    def test_length(self):
        self.assertEqual(sp.p_length.parse(":0.41"), 0.41)

    def test_format(self):
        self.assertEqual(sp.p_format.parse("[&!color=#000000]"), {"!color": "#000000"})

    def test_term(self):
        self.assertEqual(
            sp.p_term.parse("A[&!color=#0000ff]:0.42"),
            ("A", {"!color": "#0000ff"}, 0.42),
        )
        self.assertEqual(sp.p_term.parse("A:0.42"), ("A", None, 0.42))
        self.assertEqual(sp.p_term.parse("A[foo=boo]"), ("A", {"foo": "boo"}, None))
        self.assertEqual(sp.p_term.parse("A"), ("A", None, None))

    def test_info(self):
        self.assertEqual(
            sp.p_info.parse("A[&!color=#0000ff]:0.42"),
            ("A", {"!color": "#0000ff"}, 0.42),
        )
        self.assertEqual(sp.p_info.parse("A:0.42"), ("A", None, 0.42))
        self.assertEqual(sp.p_info.parse("A[foo=boo]"), ("A", {"foo": "boo"}, None))
        self.assertEqual(sp.p_info.parse(""), (None, None, None))

    def test_leaf(self):
        self.assertEqual(
            sp.p_leaf.parse("A[foo=boo]:0.42"),
            sp.Node(label="A", form={"foo": "boo"}, length=0.42),
        )

    def test_node(self):
        self.assertEqual(
            sp.p_node.parse("(A[foo=boo,bar=baz]:0.42)Root"),
            sp.Node(
                kids=[
                    sp.Node(label="A", form={"foo": "boo", "bar": "baz"}, length=0.42)
                ],
                label="Root",
            ),
        )

    def test_newick(self):
        self.assertEqual(
            sp.p_tree.parse("(A[foo=boo]:0.42)Root;").tree,
            sp.Node(
                kids=[sp.Node(label="A", form={"foo": "boo"}, length=0.42)],
                label="Root",
            ),
        )
        self.assertEqual(
            sp.p_tree.parse("(B,(A,C,E),D);").tree,
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

    def test_nexus(self):
        self.assertEqual(
            sp.p_nexus_tree_line.parse("\ttree tree_1 = [&R] (B,(A,C,E),D);\n"),
            sp.p_tree.parse("(B,(A,C,E),D);").tree,
        )

        taxa_block = "\n".join(
            [
                "\tdimensions ntax=3",
                "\ttaxlabels",
                "\t'A'",
                "\t'B'[&!color=#999999]",
                "\t'C'",
                "\t'D'",
                "\t'E'",
                ";",
            ]
        )

        self.assertEqual(sp.p_taxa_block.parse(taxa_block), dict(B="#999999"))
        taxa_section = "\n".join(
            [
                "begin taxa;",
                "\tdimensions ntax=3",
                "\ttaxlabels",
                "\t'A'",
                "\t'B'[&!color=#999999]",
                "\t'C'",
                "\t'D'",
                "\t'E'",
                ";",
                "end;" "",
            ]
        )
        self.assertEqual(
            sp.p_nexus_section.parse(taxa_section), ("taxa", dict(B="#999999"))
        )
        tree_section = "\n".join(
            [
                "begin trees;",
                "\ttree tree_1 = [&R] (B,(A,C,E),D);",
                "end;",
            ]
        )
        self.assertEqual(
            newick(sp.p_nexus_section.parse(tree_section)[1]), "(B,(A,C,E),D);"
        )

        nexus_file = "\n".join(
            [
                "#NEXUS",
                "begin taxa;",
                "\tdimensions ntax=3",
                "\ttaxlabels",
                "\t'A'",
                "\t'B'",
                "\t'C'",
                "\t'D'",
                "\t'E'",
                ";",
                "end;",
                "",
                "begin trees;",
                "\ttree tree_1 = [&R] (B,(A,C,E),D);",
                "end;",
                "",
            ]
        )
        self.assertEqual(
            sp.p_nexus.parse(nexus_file).tree, sp.p_tree.parse("(B,(A,C,E),D);").tree
        )
        self.assertEqual(
            sp.p_tree.parse(nexus_file).tree, sp.p_tree.parse("(B,(A,C,E),D);").tree
        )

        big_nexus_file = "\n".join(
            [
                """#NEXUS""",
                """begin taxa;""",
                """	dimensions ntax=6;""",
                """	taxlabels""",
                """	'X1|H'[&!color=#ff0000]""",
                """	'X2|H'""",
                """	'X3|H'""",
                """	'X4|H'""",
                """	'X5|H'""",
                """	'X6|S'""",
                """;""",
                """end;""",
                """""",
                """begin trees;""",
                """	tree tree_1 = [&R] ('X1|H':0.3,('X2|H':0.3,('X3|H':0.3,('X4|H':0.3,('X5|H':0.3,'X6|S':0.3):0.3):0.3):0.3):0.3);""",
                """end;""",
                """""",
                """begin figtree;""",
                """	set appearance.backgroundColorAttribute="Default";""",
                """	set appearance.backgroundColour=#ffffff;""",
                """	set appearance.branchColorAttribute="User selection";""",
                """	set appearance.branchColorGradient=false;""",
                """	set appearance.branchLineWidth=1.0;""",
                """	set appearance.branchMinLineWidth=0.0;""",
                """	set appearance.branchWidthAttribute="Fixed";""",
                """	set appearance.foregroundColour=#000000;""",
                """	set appearance.hilightingGradient=false;""",
                """	set appearance.selectionColour=#2d3680;""",
                """	set branchLabels.colorAttribute="User selection";""",
                """	set branchLabels.displayAttribute="Branch times";""",
                """	set branchLabels.fontName="Al Bayan";""",
                """	set branchLabels.fontSize=8;""",
                """	set branchLabels.fontStyle=0;""",
                """	set branchLabels.isShown=false;""",
                """	set branchLabels.significantDigits=4;""",
                """	set layout.expansion=0;""",
                """	set layout.layoutType="RECTILINEAR";""",
                """	set layout.zoom=0;""",
                """	set legend.attribute=null;""",
                """	set legend.fontSize=10.0;""",
                """	set legend.isShown=false;""",
                """	set legend.significantDigits=4;""",
                """	set nodeBars.barWidth=4.0;""",
                """	set nodeBars.displayAttribute=null;""",
                """	set nodeBars.isShown=false;""",
                """	set nodeLabels.colorAttribute="User selection";""",
                """	set nodeLabels.displayAttribute="Node ages";""",
                """	set nodeLabels.fontName="Al Bayan";""",
                """	set nodeLabels.fontSize=8;""",
                """	set nodeLabels.fontStyle=0;""",
                """	set nodeLabels.isShown=false;""",
                """	set nodeLabels.significantDigits=4;""",
                """	set nodeShape.colourAttribute=null;""",
                """	set nodeShape.isShown=false;""",
                """	set nodeShape.minSize=10.0;""",
                """	set nodeShape.scaleType=Width;""",
                """	set nodeShape.shapeType=Circle;""",
                """	set nodeShape.size=4.0;""",
                """	set nodeShape.sizeAttribute=null;""",
                """	set polarLayout.alignTipLabels=false;""",
                """	set polarLayout.angularRange=0;""",
                """	set polarLayout.rootAngle=0;""",
                """	set polarLayout.rootLength=100;""",
                """	set polarLayout.showRoot=true;""",
                """	set radialLayout.spread=0.0;""",
                """	set rectilinearLayout.alignTipLabels=false;""",
                """	set rectilinearLayout.curvature=0;""",
                """	set rectilinearLayout.rootLength=100;""",
                """	set scale.offsetAge=0.0;""",
                """	set scale.rootAge=1.0;""",
                """	set scale.scaleFactor=1.0;""",
                """	set scale.scaleRoot=false;""",
                """	set scaleAxis.automaticScale=true;""",
                """	set scaleAxis.fontSize=8.0;""",
                """	set scaleAxis.isShown=false;""",
                """	set scaleAxis.lineWidth=1.0;""",
                """	set scaleAxis.majorTicks=1.0;""",
                """	set scaleAxis.origin=0.0;""",
                """	set scaleAxis.reverseAxis=false;""",
                """	set scaleAxis.showGrid=true;""",
                """	set scaleBar.automaticScale=true;""",
                """	set scaleBar.fontSize=10.0;""",
                """	set scaleBar.isShown=true;""",
                """	set scaleBar.lineWidth=1.0;""",
                """	set scaleBar.scaleRange=0.0;""",
                """	set tipLabels.colorAttribute="User selection";""",
                """	set tipLabels.displayAttribute="Names";""",
                """	set tipLabels.fontName="Al Bayan";""",
                """	set tipLabels.fontSize=8;""",
                """	set tipLabels.fontStyle=0;""",
                """	set tipLabels.isShown=true;""",
                """	set tipLabels.significantDigits=4;""",
                """	set trees.order=false;""",
                """	set trees.orderType="increasing";""",
                """	set trees.rooting=false;""",
                """	set trees.rootingType="User Selection";""",
                """	set trees.transform=false;""",
                """	set trees.transformType="cladogram";""",
                """end;""",
            ]
        )
        self.assertEqual(
            sp.p_tree.parse(big_nexus_file).tree,
            sp.p_tree.parse(
                "('X1|H':0.3,('X2|H':0.3,('X3|H':0.3,('X4|H':0.3,('X5|H':0.3,'X6|S':0.3):0.3):0.3):0.3):0.3);"
            ).tree,
        )


class TestStringify(unittest.TestCase):
    def test_stringify(self):
        s = "(B|a,(A|b,C|b,E|b),D|c);"
        self.assertEqual(newick(sp.p_tree.parse(s)), s)

    def test_string_complex(self):
        s = """("that's cool"[&!color=#000000]:0.3);"""
        self.assertEqual(newick(sp.p_tree.parse(s)), s)

        s = """(A:3);"""
        self.assertEqual(newick(sp.p_tree.parse(s)), s)

        s = """('that"s !@#$%^&)(*&^[]cool'[&!color=#000000]:0.3);"""
        self.assertEqual(newick(sp.p_tree.parse(s)), s)


class TestALgorithms(unittest.TestCase):
    def test_treemap(self):
        def _lower(x):
            if x.label:
                x.label = x.label.lower()
            return x

        self.assertEqual(
            alg.treemap(sp.p_tree.parse("(B,(A,C,E),D);").tree, _lower),
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
            alg.treefold(sp.p_tree.parse("(B,(A,C,E),D);").tree, _fun, []),
            [None, "B", None, "A", "C", "E", "D"],
        )

    def test_factorByCapture(self):
        self.assertEqual(alg.factorByCaptureFun("BAD", "(A)"), "A")
        # the first match is found
        self.assertEqual(alg.factorByCaptureFun("BAD", "(A)|(B)"), "B")
        self.assertEqual(alg.factorByCaptureFun("BAD", "(A|B)"), "B")
        # the deepest match is found
        self.assertEqual(alg.factorByCaptureFun("BAD", "(B(.)|E(.))"), "A")
        self.assertEqual(alg.factorByCaptureFun("BAD", "((B(.)|E(.))|D(.))"), "A")
        # default is returned when no match is obtained
        self.assertEqual(alg.factorByCaptureFun("BAD", "(P)", default="X"), "X")

    def test_factorByLabel(self):
        def _fun(name):
            try:
                return name.split("|")[1]
            except:
                return None

        self.assertEqual(
            alg.factorByLabel(sp.p_tree.parse("(B|a,(A|b,C|b,E|b),D|c);").tree, _fun),
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
            alg.getLeftmost(sp.p_tree.parse("(B,(A,C,E),D);").tree), Node(label="B")
        )

    def test_sampleContext(self):
        self.assertEqual(
            alg.sampleContext(
                alg.factorByField(
                    sp.p_tree.parse("(B|a,(A|b,C|b,E|b),D|c);").tree, field=2
                ),
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
            alg.sampleContext(
                alg.factorByField(
                    sp.p_tree.parse("(B|a,(A|b,C|b,E|b),D|c);").tree, field=2
                ),
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
            alg.clean(sp.p_tree.parse("(B,((A)),D);").tree),
            sp.p_tree.parse("(B,A,D);").tree,
        )
        self.assertEqual(
            alg.clean(sp.p_tree.parse("(((A)));").tree), sp.p_tree.parse("(A);").tree
        )
        self.assertEqual(
            alg.clean(sp.p_tree.parse("((((((B)),((A))))));").tree),
            sp.p_tree.parse("(B,A);").tree,
        )
        self.assertEqual(
            alg.clean(sp.p_tree.parse("((((A,B))));").tree), sp.p_tree.parse("(A,B);").tree
        )
        self.assertEqual(
            alg.clean(sp.p_tree.parse("(((A,B)),((((C)))));").tree),
            sp.p_tree.parse("((A,B),C);").tree,
        )
        self.assertEqual(
            alg.clean(sp.p_tree.parse("(B:1,((A:3):2):1,D:1);").tree),
            sp.p_tree.parse("(B:1,A:6,D:1);").tree,
        )

    def test_sampleRandom(self):
        def sampleRandomSimple(node, n, rng):
            return alg.sampleRandom(
                node, rng, count_fun=lambda x: n, keep_fun=lambda x: False
            )

        self.assertEqual(
            sampleRandomSimple(
                sp.p_tree.parse("(B,(A,C,E),D);").tree, 5, rng=random.Random(42)
            ),
            sp.p_tree.parse("(B,(A,C,E),D);").tree,
        )
        self.assertEqual(
            sampleRandomSimple(
                sp.p_tree.parse("(B,(A,C,E),D);").tree, 10, rng=random.Random(42)
            ),
            sp.p_tree.parse("(B,(A,C,E),D);").tree,
        )
        self.assertEqual(
            sampleRandomSimple(
                sp.p_tree.parse("(B,(A,C,E),D);").tree, 10, rng=random.Random(42)
            ),
            sp.p_tree.parse("(B,(A,C,E),D);").tree,
        )
        self.assertEqual(
            sampleRandomSimple(
                sp.p_tree.parse("(B,(A,C,E),D);").tree, 2, rng=random.Random(42)
            ),
            sp.p_tree.parse("(B,D);").tree,
        )

    def test_sampleParaphyletic(self):
        fork = "(X1|H,(X2|H,(X3|H,(X4|H,((Y1|H,(Y2|H,(Y3|H,(Y4|H,Y5|H)))),X6|S)))));"

        forkFac = alg.factorByField(sp.p_tree.parse(fork).tree, field=2)

        self.assertEqual(
            newick(
                alg.sampleParaphyletic(
                    forkFac, proportion=0.3, keep=["S"], minTips=2, seed=42
                )
            ),
            "(X1|H,(X4|H,((Y2|H,Y3|H),X6|S)));",
        )
        self.assertEqual(
            newick(alg.sampleParaphyletic(sp.p_tree.parse(fork).tree, number=2, seed=46)),
            "(X2|H,Y2|H);",
        )

        nine = "(Y|x,(U|x,(I|x,(((A|y,B|y),C|y),(D|z,(E|z,F|z))))));"

        self.assertEqual(
            newick(alg.sampleParaphyletic(sp.p_tree.parse(nine).tree, number=1, seed=43)),
            "(A|y);",
        )
        self.assertEqual(
            newick(
                alg.sampleParaphyletic(
                    alg.factorByField(sp.p_tree.parse(nine).tree, field=2),
                    number=1,
                    seed=43,
                )
            ),
            "(I|x,(B|y,F|z));",
        )
        self.assertEqual(
            newick(
                alg.sampleParaphyletic(
                    alg.factorByField(sp.p_tree.parse(nine).tree, field=2),
                    number=2,
                    seed=43,
                )
            ),
            "(U|x,(I|x,((A|y,C|y),(E|z,F|z))));",
        )

    def test_sampleProportional(self):
        six = "(((A,B),C),(D,(E,F)));"
        # sampling is across root children
        self.assertEqual(
            newick(
                alg.sampleProportional(
                    sp.p_tree.parse(six).tree, proportion=0.1, minTips=2, seed=43
                )
            ),
            "(A,C);",
        )

        seven = "(O|x,(((A|y,B|y),C|y),(D|z,(E|z,F|z))));"
        self.assertEqual(
            newick(
                alg.sampleProportional(
                    alg.factorByField(sp.p_tree.parse(seven).tree, field=2),
                    proportion=0.1,
                    minTips=2,
                    seed=46,
                )
            ),
            "(O|x,((A|y,B|y),(D|z,F|z)));",
        )
        # --- selection by number works for unfactored trees
        # sometimes a basal strain is selected
        self.assertEqual(
            newick(alg.sampleProportional(sp.p_tree.parse(seven).tree, number=1, seed=46)),
            "(O|x);",
        )
        # sometimes it isn't (random)
        self.assertEqual(
            newick(alg.sampleProportional(sp.p_tree.parse(seven).tree, number=1, seed=44)),
            "(C|y);",
        )
        # sometimes both root branches will be sampled
        self.assertEqual(
            newick(alg.sampleProportional(sp.p_tree.parse(seven).tree, number=3, seed=46)),
            "(O|x,(C|y,F|z));",
        )
        # sometimes they won't
        self.assertEqual(
            newick(alg.sampleProportional(sp.p_tree.parse(seven).tree, number=3, seed=40)),
            "(C|y,(D|z,E|z));",
        )
        # --- selection by number works for factored trees
        self.assertEqual(
            newick(
                alg.sampleProportional(
                    alg.factorByField(sp.p_tree.parse(seven).tree, field=2),
                    number=1,
                    seed=43,
                )
            ),
            "(O|x,(A|y,E|z));",
        )
        self.assertEqual(
            newick(
                alg.sampleProportional(
                    alg.factorByField(sp.p_tree.parse(seven).tree, field=2),
                    number=2,
                    seed=43,
                )
            ),
            "(O|x,((A|y,B|y),(D|z,F|z)));",
        )
        # --- high numbers cleanly select everything
        self.assertEqual(
            newick(
                alg.sampleProportional(
                    alg.factorByField(sp.p_tree.parse(seven).tree, field=2), number=100
                )
            ),
            seven,
        )
        self.assertEqual(
            newick(
                alg.sampleProportional(
                    alg.factorByField(sp.p_tree.parse(seven).tree, field=2), number=100
                )
            ),
            seven,
        )

    def test_distribute(self):
        self.assertEqual(alg.distribute(5, 3), [2, 2, 1])
        self.assertEqual(alg.distribute(3, 5), [1, 1, 1, 0, 0])
        self.assertEqual(alg.distribute(5, 1), [5])
        self.assertEqual(alg.distribute(0, 2), [0, 0])
        self.assertEqual(alg.distribute(5, 0), [])
        self.assertEqual(alg.distribute(0, 0), [])
        # with sizes vector
        self.assertEqual(alg.distribute(10, 3, [3, 100, 1]), [3, 6, 1])
        self.assertEqual(alg.distribute(10, 3, [3, 100, 0]), [3, 7, 0])
        self.assertEqual(alg.distribute(1, 2, [0, 10]), [0, 1])

    def test_sampleN(self):
        self.assertEqual(
            newick(alg.sampleN(sp.p_tree.parse("(B,(A,C,E),D);").tree, 2)), "(B,A);"
        )


if __name__ == "__main__":
    unittest.main()
