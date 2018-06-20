import sys,logging

sys.path.append("..")
from GLRParser import *
from timeit import default_timer as timer

logging.basicConfig(level=logging.DEBUG,filename="parser.log",filemode="w")
grm_dir = "../GLRParser/grm/"

def main():
    parser = Parser("EN","TR")
    start = timer()
    parser.load_grammar(grm_dir+"tenses.grm")
    end = timer()
    print("Number of rules:",len(parser.rules))
    print("Grammar load time:", int((end-start)*1000),"ms")

    start = end
    parser.compile()
    end = timer()
    print("Number of states:",len({nstate for _,nstate in parser.dfa.items()}))
    print("Compile time:", int((end-start)*1000),"ms")

    start = end
    input_cnt,trans_cnt,match_cnt,experr_cnt,ignore_cnt = parser.trans_file(
        "test.in.txt", #grm_dir+"tenses.in.txt",
        "test.out.txt", #grm_dir+"tenses.out.txt",
        ignore_exp_error=True
    )
    end = timer()
    print("Parse time Total:", int((end-start)*1000),"ms  Per sentence:", int((end-start)*1000/input_cnt),"ms")

    print("input={}, translated={}, matched={}, experr={}, ignored={} success=%{}".format(
        input_cnt,
        trans_cnt,
        match_cnt,
        experr_cnt,
        ignore_cnt,
        (match_cnt+experr_cnt+ignore_cnt)*100//input_cnt
    ))


main()
