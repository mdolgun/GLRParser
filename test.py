from GLRParser import Parser, ParseError, GrammarError, Tree

try:
    parser = Parser() # initialize parser object

    parser.load_grammar("GLRParser\grm\simple_trans.grm") # load grammar from a file
    sent = "i saw the man in the house with the telescope" # sentence to parse

    parser.compile() # constructs parsing tables
    parser.parse(sent) # parse the sentence

    tree = parser.make_tree() # generates parse forest
    ttree = parser.trans_tree(tree) # translate the parse forest

    print(ttree.pformat(Tree.right_tree)) # pretty-print the translated parse forest

    for trans in ttree.enum(): # enumerate and print all alternative translations in the parse forest
	    print(trans.replace(" -","")) # concat suffixes
except GrammarError as ge:
    print(ge)
except ParseError as pe:
    print(pe)