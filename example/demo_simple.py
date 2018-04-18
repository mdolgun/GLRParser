import sys,logging
sys.path.append("..")

logging.basicConfig(level=logging.DEBUG,filename="parser.log",filemode="w")

from GLRParser import Parser, ParseError, GrammarError, Tree

try:
    parser = Parser() # initialize parser object

    parser.load_grammar("..\GLRParser\grm\simple.grm") # load grammar from a file
    sent = "i saw the man in the house with the telescope" # sentence to parse

    parser.compile() # constructs parsing tables
    parser.parse(sent) # parse the sentence

    tree = parser.make_tree() # generates parse forest

    print(tree.pformat()) # pretty-print the parse forest

except GrammarError as ge:
    print(ge)
except ParseError as pe:
    print(pe)