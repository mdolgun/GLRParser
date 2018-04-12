import sys
sys.path.append("..")
from GLRParser import *

grm_dir = "../GLRParser/grm/"


parser = Parser(None,None)
parser.load_grammar(grm_dir+"simple_trans.grm")
parser.compile()

rparser = Parser(None,None)
rparser.load_grammar(grm_dir+"simple_trans.grm",True)
rparser.compile()

sents = ["i saw the man in the house with the telescope", "the man with the telescope saw the man in the house"]

for sent in sents:
    parser.parse(sent)
    tree = parser.make_tree()
    ttree = parser.trans_tree(tree)
    trans = list(ttree.enum())
    print(sent)
    for rsent in trans:
        print("*",rsent)
        rparser.parse(rsent)
        rtree = rparser.make_tree()
        trtree = rparser.trans_tree(rtree)
        rtrans = list(trtree.enum())
        for rrsent in rtrans:
            print("* *",rrsent)

