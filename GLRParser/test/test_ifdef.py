import sys, unittest, textwrap
sys.path.append("../..")
from GLRParser import Parser, ParseError, GrammarError, Tree, Rule

class TestIfdef(unittest.TestCase):
    grammar = """
%ifdef token1
    %ifdef token2
        S -> in : out1
    %else
        S -> in : out2
    %endif
%else
    %ifdef token2
        S -> in : out3
    %else
        S -> in : out4
    %endif    
%endif
S -> in : out
"""
    rule_sets = [
        [
            Rule(head="S'", left=['S'], right=[0], feat={}, lparam=[{}], rparam=[{}], cost=0),
            Rule(head='S', left=['in'], right=['out1'], feat={}, lparam=[False], rparam=[False], cost=0),
            Rule(head='S', left=['in'], right=['out'], feat={}, lparam=[False], rparam=[False], cost=0),
        ],
        [
            Rule(head="S'", left=['S'], right=[0], feat={}, lparam=[{}], rparam=[{}], cost=0),
            Rule(head='S', left=['in'], right=['out2'], feat={}, lparam=[False], rparam=[False], cost=0),
            Rule(head='S', left=['in'], right=['out'], feat={}, lparam=[False], rparam=[False], cost=0),
        ],
        [
            Rule(head="S'", left=['S'], right=[0], feat={}, lparam=[{}], rparam=[{}], cost=0),
            Rule(head='S', left=['in'], right=['out3'], feat={}, lparam=[False], rparam=[False], cost=0),
            Rule(head='S', left=['in'], right=['out'], feat={}, lparam=[False], rparam=[False], cost=0),
        ],
        [
            Rule(head="S'", left=['S'], right=[0], feat={}, lparam=[{}], rparam=[{}], cost=0),
            Rule(head='S', left=['in'], right=['out4'], feat={}, lparam=[False], rparam=[False], cost=0),
            Rule(head='S', left=['in'], right=['out'], feat={}, lparam=[False], rparam=[False], cost=0),
        ],
    ]
    defines = [
        "%define token1\n%define token2\n",
        "%define token1\n",
        "%define token2\n",
        "",
    ]
    
    def test_rules(self):
        self.maxDiff = None
        for define,exp_rules in zip(self.defines,self.rule_sets):
            parser = Parser()       
            parser.load_grammar(text=define+self.grammar)            
            with self.subTest(rules=parser.rules,exp_rules=exp_rules):
                self.assertEqual(parser.rules, exp_rules)

def genTestMacro():
    for define,exp_rules in zip(TestIfdef.defines,TestIfdef.rule_sets):
        parser = Parser()       
        parser.load_grammar(text=define+TestIfdef.grammar)
        print(define)
        print(parser.rules)
        print("==============================")

 
if __name__== '__main__':
    unittest.main()
    #genTestMacro()