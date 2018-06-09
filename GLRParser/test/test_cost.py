import sys, unittest, textwrap
sys.path.append("../..")
from GLRParser import Parser, ParseError, GrammarError, Tree

class TestCost:
    def setUp(self):
        parser = Parser()
        
        parser.load_grammar(text=self.grammar,reverse=self.reverse)
        parser.compile()
        self.parser = parser
        #self.maxDiff = None

    def test_enumx(self):
        for idx,sent in enumerate(self.sents):
            with self.subTest(idx=idx,sent=sent):
                self.parser.parse(sent)
                tree = self.parser.make_tree()
                utree = self.parser.unify_tree(tree)
                ttree = self.parser.trans_tree(utree)
                self.assertEqual(list(sorted(ttree.enumx())), self.enumx[idx])

class TestCost1A(TestCost,unittest.TestCase):
    reverse = False
    grammar = """
        S -> A B : C
        A -> a0 
        A -> a1   {-1} [f=1]
        B -> b0 
        B -> b1   {-1} [f=1]
        C -> : c0 {-1} [f=0]
        C -> : c1      [f=1]    
    """
    sents = [ "a0 b0", "a0 b1", "a1 b0", "a1 b1"] 
    enumx = [
        [('c0', 0)],
        [('c1', 0)],
        [('c1', 0)],
        [('c1', 0)],
    ]
class TestCost1AR(TestCost,unittest.TestCase):
    reverse = True
    grammar = """
        S -> A B : C
        A -> a0 
        A -> a1   {-1} [f=1]
        B -> b0 
        B -> b1   {-1} [f=1]
        C -> : c0 {-1} [f=0]
        C -> : c1      [f=1] 
    """
    sents = [ "c0", "c1"] 
    enumx = [
        [('a0 b0', 0)],
        [('a1 b1', 0)],
    ]

class TestCost1B(TestCost,unittest.TestCase):
    reverse = False
    grammar = """
        S -> A B : C
        A -> a0   {1}
        A -> a1       [f=1]
        B -> b0   {1}
        B -> b1       [f=1]
        C -> : c0     [f=0]
        C -> : c1 {1} [f=1]
    """
    sents = [ "a0 b0", "a0 b1", "a1 b0", "a1 b1"] 
    enumx = [
        [('c0', 0), ('c1', 1)],
        [('c1', 1)],
        [('c1', 1)],
        [('c1', 1)],
    ]

class TestCost1BR(TestCost,unittest.TestCase):
    reverse = True
    grammar = """
        S -> A B : C
        A -> a0   {1}
        A -> a1       [f=1]
        B -> b0   {1}
        B -> b1       [f=1]
        C -> : c0     [f=0]
        C -> : c1 {1} [f=1]
    """
    sents = [ "c0", "c1"] 
    enumx = [
        [('a0 b0', 2)],
        [('a0 b0', 2), ('a0 b1', 1), ('a1 b0', 1), ('a1 b1', 0)],
    ]

class TestCost2(TestCost,unittest.TestCase):
    reverse = False
    grammar = """
        S -> A B : C
        A -> a b {-1} [f=2]
        A -> a        [f=1]
        A ->          [f=0]
        B -> a b      [g=2]
        B -> b        [g=1]
        B ->          [g=0]
        C -> : c E    [f=2]
        C -> : D c    [g=2]
        C -> : D E {1}
        D -> : dd     [f=2]
        D -> : d      [f=1]
        D ->          [f=0]
        E -> : ee     [g=2]
        E -> : e      [g=1]
        E ->          [g=0]
        """  
    sents = [ "a b", "a b b", "a a b", "a b a b"]
    enumx = [
        [('c', 0), ('c', 0), ('d e', 1), ('dd', 1), ('ee', 1)],
        [('c e', 0), ('dd e', 1)],
        [('d c', 0), ('d ee', 1)],
        [('c ee', 0), ('dd c', 0), ('dd ee', 1)],
    ]

class TestCost3(TestCost,unittest.TestCase):
    reverse = False
    grammar = """
        S -> A : A B {-1}    [f=0]
        S -> A : A n B 
        A -> a : x         [f=1]  
        A -> b : y
        B -> : z
    """
    sents = [ "a", "b" ]
    enumx = [
        [('x n z', 0)],
        [('y z', 0)],
    ]


def genTestCost(cls):
    parser = Parser()
    parser.load_grammar(text=cls.grammar,reverse=cls.reverse)
    parser.compile()
    for sent in cls.sents:
        parser.parse(sent)
        tree = parser.make_tree()
        utree = parser.unify_tree(tree)
        ttree = parser.trans_tree(utree)
        print(list(sorted(ttree.enumx())))
 
if __name__== '__main__':
    unittest.main()
    #genTestCost(TestCost3)