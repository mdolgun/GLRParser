import sys,logging
sys.path.append("../..")
from GLRParser import Parser, ParseError, GrammarError

#logging.basicConfig(level=logging.DEBUG,filename="parser.log",filemode="w")

def main():
    parser = Parser("EN","TR")
    parser.load_grammar("tenses.grm")
    parser.compile()
    input_cnt,trans_cnt,match_cnt = parser.trans_file("tenses.in.txt","tenses.out.txt")
    print("input={}, translated={}, matched={} success=%{}".format(input_cnt,trans_cnt,match_cnt,match_cnt*100//input_cnt))

main()
