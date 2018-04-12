import sys,logging
sys.path.append("..")
from GLRParser import *

logging.basicConfig(level=logging.DEBUG,filename="parser.log",filemode="w")
grm_dir = "../GLRParser/grm/"

def main():
    parser = Parser("EN","TR")
    parser.load_grammar(grm_dir+"np.grm")
    parser.compile()
    print("Translating the file...")
    input_cnt,trans_cnt,match_cnt,experr_cnt,ignore_cnt = parser.trans_file(
        grm_dir+"np.in.txt", 
        grm_dir+"np.out.txt", 
        ignore_exp_error=True
    )
    print("input={}, translated={}, matched={}, experr={}, ignored={} success=%{}".format(
        input_cnt,
        trans_cnt,
        match_cnt,
        experr_cnt,
        ignore_cnt,
        (match_cnt+experr_cnt+ignore_cnt)*100//input_cnt
    ))

main()
