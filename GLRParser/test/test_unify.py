import sys, unittest, textwrap
sys.path.append("../..")
from GLRParser import Parser, ParseError, UnifyError, GrammarError, Tree

class TestUnifyBinary(unittest.TestCase): 

    grammar = """
        S -> A B : C 
        A -> a0     
        A -> a1     [+f]
        B -> b0    
        B -> b1     [+f]
        C -> : c0   [!f]      
        C -> : c1   [?f]  
        """

    cases = [
        ("a0 b0","""\
            S(
            #1[]
                A(
                #2[]
                    a0
                )
                B(
                #4[]
                    b0
                )
            )
            """),

        ("a0 b1","""\
            S(
            #1[f=+]
                A(
                #2[]
                    a0
                )
                B(
                #5[f=+]
                    b1
                )
            )
            """),

        ("a1 b0","""\
            S(
            #1[f=+]
                A(
                #3[f=+]
                    a1
                )
                B(
                #4[]
                    b0
                )
            )
            """),

        ("a1 b1","""\
            S(
            #1[f=+]
                A(
                #3[f=+]
                    a1
                )
                B(
                #5[f=+]
                    b1
                )
            )
            """),

        ]

    def setUp(self):
        parser = Parser()

        parser.parse_grammar(text=self.grammar)
        parser.compile()
        self.parser = parser
        self.maxDiff = None

    def test_all(self):
        for idx,(sent,out) in enumerate(self.cases):
            with self.subTest(idx=idx,sent=sent):
                try:
                    self.parser.parse(sent)
                    tree = self.parser.make_tree()
                    tree2 = self.parser.unify_tree(tree)
                    out = tree2.pformat_ext()
                except UnifyError as ue:
                    out = str(ue)
                except ParseError as pe:
                    out = str(pe)
                self.assertEqual(out, textwrap.dedent(self.cases[idx][1]))

class TestUnify(unittest.TestCase): 

    grammar = """
        S -> NP(case=nom,numb,pers) VP NP(case=acc)
        NP -> i     [case=nom,numb=sing,pers=1]
        NP -> he    [case=nom,numb=sing,pers=3]
        NP -> she   [case=nom,numb=sing,pers=3]
        NP -> it    [case=nom,numb=sing,pers=3]
        NP -> we    [case=nom,numb=plur,pers=1]
        NP -> you   [case=nom,numb=plur,pers=2]
        NP -> they  [case=nom,numb=plur,pers=3]

        NP -> me    [case=acc,numb=sing,pers=1]
        NP -> him   [case=acc,numb=sing,pers=3]
        NP -> her   [case=acc,numb=sing,pers=3]
        NP -> it    [case=acc,numb=sing,pers=3]
        NP -> us    [case=acc,numb=plur,pers=1]
        NP -> you   [case=acc,numb=plur,pers=2]
        NP -> them  [case=acc,numb=plur,pers=3]

        NP -> Det Noun  [pers=3]

        Det -> this   [numb=sing]
        Det -> these  [numb=plur]
        Det -> a      [numb=sing]
        Det -> two    [numb=plur]
        Det -> the
        Det ->

        Noun -> man   [numb=sing]
        Noun -> men   [numb=plur]

        VP -> am  Ving  [numb=sing,pers=1]
        VP -> is  Ving  [numb=sing,pers=3]
        VP -> are Ving  [numb=plur]

        VP -> was  Ving [numb=sing]
        VP -> were Ving [numb=plur]

        VP -> Ved
        VP -> V         [numb=sing,pers=1]
        VP -> Vs        [numb=sing,pers=3]
        VP -> V         [numb=plur]

        V    -> watch
        Vs   -> watches
        Ving -> watching
        Ved  -> watched
        """

    cases = [
        ("i am watching her","""\
            S(
            #1[numb=sing,pers=1]
                NP(
                #2[case=nom,numb=sing,pers=1]
                    i
                )
                VP(
                #25[numb=sing,pers=1]
                    am
                    Ving(
                    #36[]
                        watching
                    )
                )
                NP(
                #11[case=acc,numb=sing,pers=3]
                    her
                )
            )
            """),
        ("she is watching me","""\
            S(
            #1[numb=sing,pers=3]
                NP(
                #4[case=nom,numb=sing,pers=3]
                    she
                )
                VP(
                #26[numb=sing,pers=3]
                    is
                    Ving(
                    #36[]
                        watching
                    )
                )
                NP(
                #9[case=acc,numb=sing,pers=1]
                    me
                )
            )
            """ ),
        ("these men are watching us","""\
            S(
            #1[numb=plur,pers=3]
                NP(
                #16[numb=plur,pers=3]
                    Det(
                    #18[numb=plur]
                        these
                    )
                    Noun(
                    #24[numb=plur]
                        men
                    )
                )
                VP(
                #27[numb=plur]
                    are
                    Ving(
                    #36[]
                        watching
                    )
                )
                NP(
                #13[case=acc,numb=plur,pers=1]
                    us
                )
            )
            """ ),
        ("me am watching you", "UnifyU precheck error feat=case src=acc param=nom super=S#1 sub=NP#9"),
        ("she is watching i", "UnifyU precheck error feat=case src=nom param=acc super=S#1 sub=NP#2"),
        ("two man is watching it", "UnifyU error feat=numb src=sing dst=plur super=NP#16 sub=Noun#23"),
        ("a man watch us","UnifyU error feat=pers src=1 dst=3 super=S#1 sub=VP#31"),
        ("they watch us","""\
            S(
            #1[numb=plur,pers=3]
                NP(
                #8[case=nom,numb=plur,pers=3]
                    they
                )
                VP(
                #33[numb=plur]
                    V(
                    #34[]
                        watch
                    )
                )
                NP(
                #13[case=acc,numb=plur,pers=1]
                    us
                )
            )
            """ ),

        ("he watches the men","""\
            S(
            #1[numb=sing,pers=3]
                NP(
                #3[case=nom,numb=sing,pers=3]
                    he
                )
                VP(
                #32[numb=sing,pers=3]
                    Vs(
                    #35[]
                        watches
                    )
                )
                NP(
                #16[numb=plur,pers=3]
                    Det(
                    #21[]
                        the
                    )
                    Noun(
                    #24[numb=plur]
                        men
                    )
                )
            )
            """ ),
        ("he watches a men","UnifyU error feat=numb src=plur dst=sing super=NP#16 sub=Noun#24")
        ]

    def setUp(self):
        parser = Parser()

        parser.parse_grammar(text=self.grammar)
        parser.compile()
        self.parser = parser
        self.maxDiff = None

    def test_all(self):
        for idx,(sent,out) in enumerate(self.cases):
            with self.subTest(idx=idx,sent=sent):
                try:
                    self.parser.parse(sent)
                    tree = self.parser.make_tree()
                    tree2 = self.parser.unify_tree(tree)
                    out = tree2.pformat_ext()
                except UnifyError as ue:
                    out = str(ue)
                except ParseError as pe:
                    out = str(pe)
                self.assertEqual(out, textwrap.dedent(self.cases[idx][1]))

def gen_TestUnify():
    parser = Parser()

    parser.parse_grammar(text=TestUnify.grammar)
    parser.compile()
    sents = ["i am watching her", "she is watching me", "these men are watching us", "me am watching you", "she is watching i", "two man is watching it",
             "a man watch us", "they watch us", "he watches the men", "he watches a men", "i watch him"]
    for sent in sents:
        print(sent)
        try:
            parser.parse(sent)
            tree = parser.make_tree()
            tree2 = parser.unify_tree(tree)
            print(tree2.pformat_ext())
        except UnifyError as ue:
            print(ue)
        except ParseError as pe:
            print(pe)

def gen_TestUnifyBinary():
    parser = Parser()

    parser.parse_grammar(text=TestUnifyBinary.grammar)
    parser.compile()
    sents = [ "a0 b0", "a0 b1", "a1 b0", "a1 b1" ]

    for sent in sents:
        print(sent)
        try:
            parser.parse(sent)
            tree = parser.make_tree()
            tree2 = parser.unify_tree(tree)
            print(tree2.pformat_ext())
        except UnifyError as ue:
            print(ue)
        except ParseError as pe:
            print(pe)
if __name__ == '__main__':
    unittest.main(verbosity=2)
    #gen_TestUnifyBinary()