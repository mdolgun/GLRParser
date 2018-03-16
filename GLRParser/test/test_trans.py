import sys, unittest, textwrap
sys.path.append("../..")
from GLRParser import Parser, ParseError, GrammarError, Tree

class TestTrans(unittest.TestCase):
    grammar = """
        S -> NP VP : NP VP
        S -> S in NP : NP -de S 
        S -> S with NP : NP -la S 
        NP -> i : 
        NP -> the man : adam
        NP -> the telescope : teleskop
        NP -> the house : ev
        NP -> NP-1 in NP-2 : NP-2 -deki NP-1
        NP -> NP-1 with NP-2 : NP-2 -lu NP-1
        VP -> saw NP : NP -ı gördüm
    """
    pformat = """\
        S(
            NP(teleskop)
            -la
            S(
                NP(ev)
                -de
                S(
                    NP()
                    VP(
                        NP(adam)
                        -ı
                        gördüm
                    )
                )
            |
                NP()
                VP(
                    NP(
                        NP(ev)
                        -deki
                        NP(adam)
                    )
                    -ı
                    gördüm
                )
            )
        |
            NP(
                NP(teleskop)
                -lu
                NP(ev)
            )
            -de
            S(
                NP()
                VP(
                    NP(adam)
                    -ı
                    gördüm
                )
            )
        |
            NP()
            VP(
                NP(
                    NP(teleskop)
                    -lu
                    NP(
                        NP(ev)
                        -deki
                        NP(adam)
                    )
                |
                    NP(
                        NP(teleskop)
                        -lu
                        NP(ev)
                    )
                    -deki
                    NP(adam)
                )
                -ı
                gördüm
            )
        )
        """
  
    #[[['teleskop', '-la', [['ev', '-de', 'adam', '-ı', 'gördüm'], ['ev', '-deki', 'adam', '-ı', 'gördüm']]], ['teleskop', '-lu', 'ev', '-de', 'adam', '-ı', 'gördüm'], [[['teleskop', '-lu', 'ev', '-deki', 'adam'], ['teleskop', '-lu', 'ev', '-deki', 'adam']], '-ı', 'gördüm']]]

    format = "S(NP(teleskop) -la S(NP(ev) -de S(NP() VP(NP(adam) -ı gördüm))|NP() VP(NP(NP(ev) -deki NP(adam)) -ı gördüm))|NP(NP(teleskop) -lu NP(ev)) -de S(NP() VP(NP(adam) -ı gördüm))|NP() VP(NP(NP(teleskop) -lu NP(NP(ev) -deki NP(adam))|NP(NP(teleskop) -lu NP(ev)) -deki NP(adam)) -ı gördüm))"
    str_format = "(teleskop -la (ev -de  adam -ı gördüm| ev -deki adam -ı gördüm)|teleskop -lu ev -de  adam -ı gördüm| (teleskop -lu ev -deki adam|teleskop -lu ev -deki adam) -ı gördüm)"
    enum = ['teleskopla evde adamı gördüm', 'teleskopla evdeki adamı gördüm', 'teleskoplu evde adamı gördüm', 'teleskoplu evdeki adamı gördüm', 'teleskoplu evdeki adamı gördüm']

    def setUp(self):
        parser = Parser()
        grammar = textwrap.dedent(self.grammar)

        parser.load_grammar(text=grammar)
        sent = "i saw the man in the house with the telescope"

        parser.compile()
        parser.parse(sent)

        self.parser = parser
        self.tree = parser.make_tree()
        self.ttree = parser.trans_tree(self.tree)
        self.maxDiff = None

    def test_enum(self):
        self.assertEqual([self.parser.post_processor(trans) for trans in self.ttree.enum()], self.enum)

    def test_format(self):
        self.assertEqual(self.ttree.format(False), self.format)

    def test_str_format(self):
        self.assertEqual(self.ttree.str_format(False), self.str_format)

    def test_pformat(self):
        self.assertEqual(self.ttree.pformat(False), textwrap.dedent(self.pformat))
                         
def main():
    # used for data generation
    grammar = """
        S -> NP VP : NP VP
        S -> S in NP : NP -de S 
        S -> S with NP : NP -la S 
        NP -> i : 
        NP -> the man : adam
        NP -> the telescope : teleskop
        NP -> the house : ev
        NP -> NP-1 in NP-2 : NP-2 -deki NP-1
        NP -> NP-1 with NP-2 : NP-2 -lu NP-1
        VP -> saw NP : NP -ı gördüm
    """
    parser = Parser()
    parser.load_grammar(text=grammar)
    sent = "i saw the man in the house with the telescope"

    parser.compile()

    parser.parse(sent)
    tree = parser.make_tree()
    ttree = parser.trans_tree(tree)
    print(ttree.format(3))
    print(ttree.pformat(3))
    print(ttree.str_format(3))
    lst = ttree.list_format(3)
    print(Tree.convert_tree(lst).replace(" -",""))
    trans_list = [parser.post_processor(trans) for trans in ttree.enum()]

    print(trans_list)

if __name__== '__main__':
    unittest.main()
    #main()