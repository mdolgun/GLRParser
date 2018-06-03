import sys
sys.path.append("..")

from GLRParser import Parser, ParseError, GrammarError, Tree

grammar = """
S -> i    V : V  +aorist -Hm
S -> you  V : V  +aorist -sHn
S -> he  Vs : Vs +aorist
S -> she Vs : Vs +aorist
S -> it  Vs : Vs +aorist
S -> we   V : V  +aorist -Hz
S -> they V : V  +aorist -lAr

S -> i am Ven     : Ven +passive -Hr -Hm
S -> you are Ven  : Ven +passive -Hr -sHn
S -> he is Ven    : Ven +passive -Hr
S -> she is Ven   : Ven +passive -Hr
S -> it is Ven    : Ven +passive -Hr
S -> we are Ven   : Ven +passive -Hr -Hz
S -> they are Ven : Ven +passive -Hr -lAr

%macro V -> V,Vs,Ving,Ved,Ven
%form V -> watch,watches,watching,watched,watched
%form V -> go,goes,going,went,gone

%suffix_macro V -> base,aorist,caus,passive
%suffix V -> izle,izler,izlet,izlen
%suffix V -> seyret,seyreder,seyrettir,seyredil
%suffix V -> git,gider,götür,gidil

$V -> $watch : izle | seyret
$V -> $go    : git
"""

try:
    parser = Parser("EN","TR") # initialize parser object

    parser.load_grammar(text=grammar) # load grammar from a text
    sent = "i watch" # sentence to parse

    parser.compile() # constructs parsing tables
    parser.parse(sent) # parse the sentence

    tree = parser.make_tree() # generates parse forest
    ttree = parser.trans_tree(tree) # translate the parse forest

    print(ttree.pformatr()) # pretty-print the translated parse forest

    for trans in ttree.enum(): # enumerate and print all alternative translations in the parse forest
        print(trans) # raw outpu
        print(parser.post_processor(trans)) # postprocessed output
except GrammarError as ge:
    print(ge)
except ParseError as pe:
    print(pe)