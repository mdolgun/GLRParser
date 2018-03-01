import sys, unittest, textwrap
sys.path.append("../..")
from GLRParser import Parser, ParseError, GrammarError, Tree

class TestParse(unittest.TestCase):
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

    pformat = """        S(
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

    pformat_ext = """        S(
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

        parser.load_grammar(text=grammar)
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

if __name__ == '__main__':
    unittest.main()