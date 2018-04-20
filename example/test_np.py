import sys,logging
from timeit import default_timer as timer
sys.path.append("..")
from GLRParser import *

logging.basicConfig(level=logging.DEBUG,filename="parser.log",filemode="w")
grm_dir = "../GLRParser/grm/"

Grammar.enable_trie = False

def main():
    start = timer()
    parser = Parser("EN","TR")
    parser.load_grammar(grm_dir+"np.grm")
    parser.compile()
    end = timer()
    print("Grammar=",end-start)
    print("Translating the file...")
    start = timer()
    input_cnt,trans_cnt,match_cnt,experr_cnt,ignore_cnt = parser.trans_file(
        grm_dir+"np.in.txt", 
        grm_dir+"np.out.txt", 
        ignore_exp_error=True
    )
    end = timer()
    print("Grammar=",end-start)
    print("input={}, translated={}, matched={}, experr={}, ignored={} success=%{}".format(
        input_cnt,
        trans_cnt,
        match_cnt,
        experr_cnt,
        ignore_cnt,
        (match_cnt+experr_cnt+ignore_cnt)*100//input_cnt
    ))

main()
