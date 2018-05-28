import sys, unittest, textwrap
sys.path.append("../..")
from GLRParser import Parser, ParseError, GrammarError, Tree, Rule

class TestMacro(unittest.TestCase):
    grammar = """
S -> V    : V    
S -> Vs   : Vs   
S -> Ving : Ving 
S -> Ved  : Ved  
S -> Ven  : Ven 
%macro V -> V,Vs,Ving,Ved,Ven
%form  V -> turn,turns,turning,turned,turned
%form  V -> go,goes,going,went,gone
$V -> $turn : dön
$V -> $go   : git
"""
    rules = [
        Rule(head="S'", left=['S'], right=[0], feat={}, lparam=[{}], rparam=[{}], cost=0),
        Rule(head='S', left=['V'], right=[0], feat={}, lparam=[None], rparam=[None], cost=0),
        Rule(head='S', left=['Vs'], right=[0], feat={}, lparam=[None], rparam=[None], cost=0),
        Rule(head='S', left=['Ving'], right=[0], feat={}, lparam=[None], rparam=[None], cost=0),
        Rule(head='S', left=['Ved'], right=[0], feat={}, lparam=[None], rparam=[None], cost=0),
        Rule(head='S', left=['Ven'], right=[0], feat={}, lparam=[None], rparam=[None], cost=0),
        Rule(head='V', left=['turn'], right=['dön'], feat={}, lparam=[False], rparam=[False], cost=0),
        Rule(head='Vs', left=['turns'], right=['dön'], feat={}, lparam=[False], rparam=[False], cost=0),
        Rule(head='Ving', left=['turning'], right=['dön'], feat={}, lparam=[False], rparam=[False], cost=0),
        Rule(head='Ved', left=['turned'], right=['dön'], feat={}, lparam=[False], rparam=[False], cost=0),
        Rule(head='Ven', left=['turned'], right=['dön'], feat={}, lparam=[False], rparam=[False], cost=0),
        Rule(head='V', left=['go'], right=['git'], feat={}, lparam=[False], rparam=[False], cost=0),
        Rule(head='Vs', left=['goes'], right=['git'], feat={}, lparam=[False], rparam=[False], cost=0),
        Rule(head='Ving', left=['going'], right=['git'], feat={}, lparam=[False], rparam=[False], cost=0),
        Rule(head='Ved', left=['went'], right=['git'], feat={}, lparam=[False], rparam=[False], cost=0),
        Rule(head='Ven', left=['gone'], right=['git'], feat={}, lparam=[False], rparam=[False], cost=0),
    ]
    def setUp(self):
        parser = Parser()
        
        parser.load_grammar(text=self.grammar)
        parser.compile()
        self.parser = parser
        #self.maxDiff = None

    def test_rules(self):
        for rule,exp_rule in zip(self.parser.rules,self.rules):
            with self.subTest(rule=rule,exp_rule=exp_rule):
                self.assertEqual(rule, exp_rule)

def genTestMacro():
    parser = Parser()
    parser.load_grammar(text=TestMacro.grammar)
    for rule in parser.rules:
        print(rule)
 
if __name__== '__main__':
    unittest.main()
    #genTestMacro()