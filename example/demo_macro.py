import sys
sys.path.append("..")

from GLRParser import Parser, ParseError, GrammarError, Tree

grammar = """
S -> Subj VP : Subj VP
VP -> V    : V    
VP -> Vs   : Vs   -Ar
VP -> Ving : Ving -Hyor
VP -> Ved  : Ved  -dH
VP -> Ven  : Ven  -mHş
%macro V -> V,Vs,Ving,Ved,Ven
%form  V -> turn,turns,turning,turned,turned
$V -> $turn          : dön
$V -> $turn Obj      : Obj çevir
$V -> $turn Obj down : Obj reddet
$V -> $turn down Obj : Obj reddet
Subj -> he
Obj  -> it : onu
"""

try:
    parser = Parser() # initialize parser object

    parser.load_grammar(text=grammar) # load grammar from a file
    sent = "he turned it down" # sentence to parse

    print(parser.format_rules())

    parser.compile() # constructs parsing tables
    parser.parse(sent) # parse the sentence

    tree = parser.make_tree() # generates parse forest
    ttree = parser.trans_tree(tree) # translate the parse forest

    print(ttree.pformatr()) # pretty-print the translated parse forest

    for trans in ttree.enum(): # enumerate and print all alternative translations in the parse forest
	    print(trans.replace(" -","")) # concat suffixes
except GrammarError as ge:
    print(ge)
except ParseError as pe:
    print(pe)