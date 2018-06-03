import sys
sys.path.append("..")

from GLRParser import Parser, ParseError, GrammarError, Tree

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
defines = [
    "%define token1\n%define token2\n",
    "%define token1\n",
    "%define token2\n",
    "",
]
for define in defines:
    parser = Parser()
    print(define)
    parser.load_grammar(text=define+grammar) 
    print(parser.format_rules())
