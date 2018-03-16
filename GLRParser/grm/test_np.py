import sys,logging
sys.path.append("../..")
from GLRParser import Parser, ParseError, GrammarError

logging.basicConfig(level=logging.DEBUG,filename="parser.log",filemode="w")

def main():
    parser = Parser("EN","TR")
    parser.load_grammar("np.grm")
    parser.compile()
    input_cnt,trans_cnt,match_cnt,experr_cnt = parser.trans_file("np.in.txt","np.out.txt")
    print("input={}, translated={}, matched={}, exp_err={} success=%{}".format(input_cnt,trans_cnt,match_cnt,experr_cnt,(match_cnt+experr_cnt)*100//input_cnt))

def main2():
    parser = Parser("EN","TR")
    parser.load_grammar("np.grm")
    parser.compile()
    sents = ["house","door bell", "house door bell","butter","butter box","house butter","house butter box"]
    #sents = ["door bell"]
    for sent in sents:
        try:
            print(sent)
            parser.parse(sent)
            tree = parser.make_tree()
            utree = parser.unify_tree(tree)
            ttree = parser.trans_tree(utree)
            #print(tree.pformat())
            #print(tree.pformat_ext())
            #print(ttree.pformat_ext(False))
            for item in ttree.enum():
                print("*",item)
        except ParseError as pe:
            print("*",pe)
main()
