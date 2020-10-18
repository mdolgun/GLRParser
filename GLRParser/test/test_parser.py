import sys, unittest, textwrap
sys.path.append("../..")
from GLRParser import Parser, ParseError, GrammarError, Tree

class TestParseSimple(unittest.TestCase):
    grammar = """
        S -> NP VP
        S -> S PP
        NP -> i 
        NP -> the man
        NP -> the telescope 
        NP -> the house 
        NP -> NP PP 
        PP -> in NP 
        PP -> with NP
        VP -> saw NP"""

    pformat = """\
        S(
            S(
                S(
                    NP(i)
                    VP(
                        saw
                        NP(the man)
                    )
                )
                PP(
                    in
                    NP(the house)
                )
            |
                NP(i)
                VP(
                    saw
                    NP(
                        NP(the man)
                        PP(
                            in
                            NP(the house)
                        )
                    )
                )
            )
            PP(
                with
                NP(the telescope)
            )
        |
            NP(i)
            VP(
                saw
                NP(
                    NP(
                        NP(the man)
                        PP(
                            in
                            NP(the house)
                        )
                    )
                    PP(
                        with
                        NP(the telescope)
                    )
                |
                    NP(the man)
                    PP(
                        in
                        NP(
                            NP(the house)
                            PP(
                                with
                                NP(the telescope)
                            )
                        )
                    )
                )
            )
        |
            S(
                NP(i)
                VP(
                    saw
                    NP(the man)
                )
            )
            PP(
                in
                NP(
                    NP(the house)
                    PP(
                        with
                        NP(the telescope)
                    )
                )
            )
        )
        """

    pformat_ext = """\
        S(
        #2[]
            S(
            #2[]
                S(
                #1[]
                    NP(
                    #3[]
                        i
                    )
                    VP(
                    #10[]
                        saw
                        NP(
                        #4[]
                            the man
                        )
                    )
                )
                PP(
                #8[]
                    in
                    NP(
                    #6[]
                        the house
                    )
                )
            |
            #1[]
                NP(
                #3[]
                    i
                )
                VP(
                #10[]
                    saw
                    NP(
                    #7[]
                        NP(
                        #4[]
                            the man
                        )
                        PP(
                        #8[]
                            in
                            NP(
                            #6[]
                                the house
                            )
                        )
                    )
                )
            )
            PP(
            #9[]
                with
                NP(
                #5[]
                    the telescope
                )
            )
        |
        #1[]
            NP(
            #3[]
                i
            )
            VP(
            #10[]
                saw
                NP(
                #7[]
                    NP(
                    #7[]
                        NP(
                        #4[]
                            the man
                        )
                        PP(
                        #8[]
                            in
                            NP(
                            #6[]
                                the house
                            )
                        )
                    )
                    PP(
                    #9[]
                        with
                        NP(
                        #5[]
                            the telescope
                        )
                    )
                |
                #7[]
                    NP(
                    #4[]
                        the man
                    )
                    PP(
                    #8[]
                        in
                        NP(
                        #7[]
                            NP(
                            #6[]
                                the house
                            )
                            PP(
                            #9[]
                                with
                                NP(
                                #5[]
                                    the telescope
                                )
                            )
                        )
                    )
                )
            )
        |
        #2[]
            S(
            #1[]
                NP(
                #3[]
                    i
                )
                VP(
                #10[]
                    saw
                    NP(
                    #4[]
                        the man
                    )
                )
            )
            PP(
            #8[]
                in
                NP(
                #7[]
                    NP(
                    #6[]
                        the house
                    )
                    PP(
                    #9[]
                        with
                        NP(
                        #5[]
                            the telescope
                        )
                    )
                )
            )
        )
        """


    format = "S(S(S(NP(i) VP(saw NP(the man))) PP(in NP(the house))|NP(i) VP(saw NP(NP(the man) PP(in NP(the house))))) PP(with NP(the telescope))|NP(i) VP(saw NP(NP(NP(the man) PP(in NP(the house))) PP(with NP(the telescope))|NP(the man) PP(in NP(NP(the house) PP(with NP(the telescope))))))|S(NP(i) VP(saw NP(the man))) PP(in NP(NP(the house) PP(with NP(the telescope)))))"
    str_format = "((i saw the man in the house|i saw the man in the house) with the telescope|i saw (the man in the house with the telescope|the man in the house with the telescope)|i saw the man in the house with the telescope)"

    def setUp(self):
        parser = Parser()
        grammar = textwrap.dedent(self.grammar)

        parser.parse_grammar(text=grammar)
        sent = "i saw the man in the house with the telescope"

        parser.compile()
        parser.parse(sent)

        self.parser = parser
        self.tree = parser.make_tree()
        self.maxDiff = None

    def test_format(self):
        self.assertEqual(self.tree.format(), self.format)

    def test_str_format(self):
        self.assertEqual(self.tree.str_format(), self.str_format)

    def test_pformat(self):
        self.assertEqual(self.tree.pformat(), textwrap.dedent(self.pformat))
                         
    def test_pformat_ext(self):
        self.assertEqual(self.tree.pformat_ext(), textwrap.dedent(self.pformat_ext))

class TestParseSimpleEmpty(unittest.TestCase):
    grammar = """
        S -> NP VP PPS
        VP -> saw NP
        NP -> BNP PPS
        PPS -> PP PPS
        PPS ->
        PP -> in NP
        PP -> with NP
        BNP -> i
        BNP -> man
        BNP -> tel
        BNP -> apt"""

    pformat = """\
        S(
            NP(
                BNP(i)
                PPS()
            )
            VP(
                saw
                NP(
                    BNP(man)
                    PPS(
                        PP(
                            in
                            NP(
                                BNP(apt)
                                PPS()
                            )
                        )
                        PPS()
                    )
                )
            )
            PPS(
                PP(
                    with
                    NP(
                        BNP(tel)
                        PPS()
                    )
                )
                PPS()
            )
        |
            NP(
                BNP(i)
                PPS()
            )
            VP(
                saw
                NP(
                    BNP(man)
                    PPS()
                )
            )
            PPS(
                PP(
                    in
                    NP(
                        BNP(apt)
                        PPS()
                    )
                )
                PPS(
                    PP(
                        with
                        NP(
                            BNP(tel)
                            PPS()
                        )
                    )
                    PPS()
                )
            |
                PP(
                    in
                    NP(
                        BNP(apt)
                        PPS(
                            PP(
                                with
                                NP(
                                    BNP(tel)
                                    PPS()
                                )
                            )
                            PPS()
                        )
                    )
                )
                PPS()
            )
        |
            NP(
                BNP(i)
                PPS()
            )
            VP(
                saw
                NP(
                    BNP(man)
                    PPS(
                        PP(
                            in
                            NP(
                                BNP(apt)
                                PPS()
                            )
                        )
                        PPS(
                            PP(
                                with
                                NP(
                                    BNP(tel)
                                    PPS()
                                )
                            )
                            PPS()
                        )
                    |
                        PP(
                            in
                            NP(
                                BNP(apt)
                                PPS(
                                    PP(
                                        with
                                        NP(
                                            BNP(tel)
                                            PPS()
                                        )
                                    )
                                    PPS()
                                )
                            )
                        )
                        PPS()
                    )
                )
            )
            PPS()
        )
        """
    pformat_ext = """\
        S(
        #1[]
            NP(
            #3[]
                BNP(
                #8[]
                    i
                )
                PPS(
                #5[]
                )
            )
            VP(
            #2[]
                saw
                NP(
                #3[]
                    BNP(
                    #9[]
                        man
                    )
                    PPS(
                    #4[]
                        PP(
                        #6[]
                            in
                            NP(
                            #3[]
                                BNP(
                                #11[]
                                    apt
                                )
                                PPS(
                                #5[]
                                )
                            )
                        )
                        PPS(
                        #5[]
                        )
                    )
                )
            )
            PPS(
            #4[]
                PP(
                #7[]
                    with
                    NP(
                    #3[]
                        BNP(
                        #10[]
                            tel
                        )
                        PPS(
                        #5[]
                        )
                    )
                )
                PPS(
                #5[]
                )
            )
        |
        #1[]
            NP(
            #3[]
                BNP(
                #8[]
                    i
                )
                PPS(
                #5[]
                )
            )
            VP(
            #2[]
                saw
                NP(
                #3[]
                    BNP(
                    #9[]
                        man
                    )
                    PPS(
                    #5[]
                    )
                )
            )
            PPS(
            #4[]
                PP(
                #6[]
                    in
                    NP(
                    #3[]
                        BNP(
                        #11[]
                            apt
                        )
                        PPS(
                        #5[]
                        )
                    )
                )
                PPS(
                #4[]
                    PP(
                    #7[]
                        with
                        NP(
                        #3[]
                            BNP(
                            #10[]
                                tel
                            )
                            PPS(
                            #5[]
                            )
                        )
                    )
                    PPS(
                    #5[]
                    )
                )
            |
            #4[]
                PP(
                #6[]
                    in
                    NP(
                    #3[]
                        BNP(
                        #11[]
                            apt
                        )
                        PPS(
                        #4[]
                            PP(
                            #7[]
                                with
                                NP(
                                #3[]
                                    BNP(
                                    #10[]
                                        tel
                                    )
                                    PPS(
                                    #5[]
                                    )
                                )
                            )
                            PPS(
                            #5[]
                            )
                        )
                    )
                )
                PPS(
                #5[]
                )
            )
        |
        #1[]
            NP(
            #3[]
                BNP(
                #8[]
                    i
                )
                PPS(
                #5[]
                )
            )
            VP(
            #2[]
                saw
                NP(
                #3[]
                    BNP(
                    #9[]
                        man
                    )
                    PPS(
                    #4[]
                        PP(
                        #6[]
                            in
                            NP(
                            #3[]
                                BNP(
                                #11[]
                                    apt
                                )
                                PPS(
                                #5[]
                                )
                            )
                        )
                        PPS(
                        #4[]
                            PP(
                            #7[]
                                with
                                NP(
                                #3[]
                                    BNP(
                                    #10[]
                                        tel
                                    )
                                    PPS(
                                    #5[]
                                    )
                                )
                            )
                            PPS(
                            #5[]
                            )
                        )
                    |
                    #4[]
                        PP(
                        #6[]
                            in
                            NP(
                            #3[]
                                BNP(
                                #11[]
                                    apt
                                )
                                PPS(
                                #4[]
                                    PP(
                                    #7[]
                                        with
                                        NP(
                                        #3[]
                                            BNP(
                                            #10[]
                                                tel
                                            )
                                            PPS(
                                            #5[]
                                            )
                                        )
                                    )
                                    PPS(
                                    #5[]
                                    )
                                )
                            )
                        )
                        PPS(
                        #5[]
                        )
                    )
                )
            )
            PPS(
            #5[]
            )
        )
        """

    format = "S(NP(BNP(i) PPS()) VP(saw NP(BNP(man) PPS(PP(in NP(BNP(apt) PPS())) PPS()))) PPS(PP(with NP(BNP(tel) PPS())) PPS())|NP(BNP(i) PPS()) VP(saw NP(BNP(man) PPS())) PPS(PP(in NP(BNP(apt) PPS())) PPS(PP(with NP(BNP(tel) PPS())) PPS())|PP(in NP(BNP(apt) PPS(PP(with NP(BNP(tel) PPS())) PPS()))) PPS())|NP(BNP(i) PPS()) VP(saw NP(BNP(man) PPS(PP(in NP(BNP(apt) PPS())) PPS(PP(with NP(BNP(tel) PPS())) PPS())|PP(in NP(BNP(apt) PPS(PP(with NP(BNP(tel) PPS())) PPS()))) PPS()))) PPS())"
    str_format = "(i  saw man in apt   with tel  |i  saw man  (in apt  with tel  |in apt with tel   )|i  saw man (in apt  with tel  |in apt with tel   ) )"

    def setUp(self):
        parser = Parser()
        grammar = textwrap.dedent(self.grammar)

        parser.parse_grammar(text=grammar)
        sent = "i saw man in apt with tel"

        parser.compile()
        parser.parse(sent)

        self.parser = parser
        self.tree = parser.make_tree()
        self.maxDiff = None

    def test_format(self):
        self.assertEqual(self.tree.format(), self.format)

    def test_str_format(self):
        self.assertEqual(self.tree.str_format(), self.str_format)

    def test_pformat(self):
        self.assertEqual(self.tree.pformat(), textwrap.dedent(self.pformat))
                         
    def test_pformat_ext(self):
        self.assertEqual(self.tree.pformat_ext(), textwrap.dedent(self.pformat_ext))

class TestParseMiddleEmpty(unittest.TestCase):
    grammar = """
        S -> A B c
        A -> a
        A ->
        B -> b
        B ->
    """

    pformat = """\
        S(
            A()
            B()
            c
        )
        """

    pformat_ext = """\
        S(
        #1[]
            A(
            #3[]
            )
            B(
            #5[]
            )
            c
        )
        """

    format = "S(A() B() c)"
    str_format = "  c"

    def setUp(self):
        parser = Parser()
        grammar = textwrap.dedent(self.grammar)

        parser.parse_grammar(text=grammar)
        sent = "c"

        parser.compile()
        parser.parse(sent)

        self.parser = parser
        self.tree = parser.make_tree()
        self.maxDiff = None

    def test_format(self):
        self.assertEqual(self.tree.format(), self.format)

    def test_str_format(self):
        self.assertEqual(self.tree.str_format(), self.str_format)

    def test_pformat(self):
        self.assertEqual(self.tree.pformat(), textwrap.dedent(self.pformat))
                         
    def test_pformat_ext(self):
        self.assertEqual(self.tree.pformat_ext(), textwrap.dedent(self.pformat_ext))


def gen_TestParseSimple():
    parser = Parser()
    grammar = textwrap.dedent(TestParseSimple.grammar)

    parser.parse_grammar(text=grammar)
    sent = "i saw the man in the house with the telescope"

    parser.compile()
    parser.parse(sent)
    tree = parser.make_tree()
    print(tree.format())
    print(tree.str_format())
    print(tree.pformat())
    print(tree.pformat_ext())

def gen_TestParseSimpleEmpty():
    parser = Parser()
    grammar = textwrap.dedent(TestParseSimpleEmpty.grammar)

    parser.parse_grammar(text=grammar)
    sent = "i saw man in apt with tel"

    parser.compile()
    parser.parse(sent)
    tree = parser.make_tree()
    print(tree.format())
    print(tree.str_format())
    print(tree.pformat())
    print(tree.pformat_ext())

def gen_TestParseMiddleEmpty():
    parser = Parser()
    grammar = textwrap.dedent(TestParseMiddleEmpty.grammar)

    parser.parse_grammar(text=grammar)
    sent = "c"

    parser.compile()
    parser.parse(sent)
    tree = parser.make_tree()
    print(tree.format())
    print(tree.str_format())
    print(tree.pformat())
    print(tree.pformat_ext())

if __name__ == '__main__':
    unittest.main()
    #gen_TestParseMiddleEmpty()