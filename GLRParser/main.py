""" A GLR Parser for Natural Language Processing and Translation

(c) 2020 by Mehmet Dolgun, m.dolgun@yahoo.com

This file is defines a main program to test a grammar using a batch input file or interactively

Command Line Usage:

USAGE1: python test_file.py <grammar_file> <input_file>
    e.g. python test_file.py main.grm main   
        * Loads and compiles the grammar file "main.grm"
        * Loads the input file "main.in.txt"
        * Translates each sentence in the input files and compares with the expected translation
        * Writes all translations and the results to the file "main.out.txt"
    Input file should consist of lines of the format: 
        <source_sentence> @ <translation> ("|" <alternate_translations>)* | "*"
        only-whitespace lines or lines starting with "#" are ignored
    e.g. a glass of water @ bir bardak su | bir su bardağı

USAGE2: python test_grm.py <grammar_file> -i
    e.g. python test_file.py main.grm -i
        * Loads and compiles the grammar file "main.grm"
        * Gets a sentence from the standard input
        * Translates the sentence and write translation to the standard out
        * Exits on empty input

USAGE3: python test_grm.py <grammar_file> -s
    e.g. python test_file.py main.grm -s
        * Loads and compiles the grammar file "main.grm"
        * Saves the compiled grammar "main.grmc"
  
"""
import sys,logging,os
import os.path 

#sys.path.append(".")
#if __name__ == "__main__":
#    from parser import Parser 
#else:
#    from .parser import Parser

if os.path.dirname(__file__) == os.getcwd(): # file is run directly from the source directory
    sys.path.append(os.path.join(os.path.dirname(__file__),".."))
from GLRParser.parser import Parser


if sys.version_info >= (3, 7):
    from time import perf_counter_ns as timer
    def timer_delta(start,end,divider=1):
        return f'{(end-start)//(1000*divider):,}'
else:
    from time import perf_counter as timer
    def timer_delta(start,end,divider=1):
        return f'{int((end-start)*1000000/divider):,}'

#logging.basicConfig(level=logging.ERROR,filename="parser.log",filemode="w")
logging.getLogger().setLevel(logging.CRITICAL)

def trans_file(grm_fname, io_fname, ignore_exp_error=False):
    """ parses all sentences in infile. Each line should be in the form: InputSentence [ "@" ExpectedTranslation ( "|" AlternateTranslation )* ]
    input and corresponding translations are written to output file. The file is appended by statistics (InputCount,TranslatedCount,MatchedCount,ExpectedErrorCount,IgnoredCount)
    """

    input_cnt = 0
    trans_cnt = 0
    match_cnt = 0
    experr_cnt = 0
    ignore_cnt = 0

    parser = Parser("EN","TR")

    with open(f"{io_fname}.in.txt", 'r', encoding="utf-8") as fin, open(f"{io_fname}.out.txt", 'w', encoding="utf-8") as fout:
        
        if grm_fname.endswith(".grmc"):
            start = timer()
            parser.load_grammar(grm_fname)
            end = timer()
            print("Grammar load time:",  timer_delta(start,end), "mics")
        else:
            start = timer()
            parser.parse_grammar(grm_fname)
            end = timer()
            print("Grammar parse time:",  timer_delta(start,end), "mics")

            start = end
            parser.compile()
            end = timer()
            print("Compile time:",  timer_delta(start,end), "mics")

        print("Number of rules:", len(parser.rules))
        print("Number of states:", len({nstate for _,nstate in parser.dfa.items()}))
        print("Number of symbols:", len({symbol for (state,symbol),nstate in parser.dfa.items()}))
        print("Number of NonTerm symbols:", len(parser.ruledict))
        print(file=fout)

        for line in fin:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            input_cnt += 1
            parts = line.split('@')
            sent = parts[0]
            if len(parts) == 2: # input file contains the expected translation
                trans = [tsent.strip() for tsent in parts[1].split('|')]
            else:
                trans = []

            sent = sent.strip()
                        
            print(" @ ".join([sent.strip()," | ".join(trans)]), file=fout)
                
            trans_list = parser.trans_sent(sent)
            if type(trans_list)==str: # an error occured
                if '*' in trans:
                    experr_cnt += 1
                    print("  EXPECTED", file=fout,end=" ")
                else:
                    print(" ", file=fout, end=" ")
                print(trans_list, file=fout)
            else:
                for alt,cost in trans_list:
                    print("  *", alt, " {", cost, "}", sep="", file=fout)

                trans_sent, trans_cost = zip(*trans_list)
                trans_cnt += 1
                if trans==[] or trans==['*'] and ignore_exp_error:
                    print("  IGNORED", file=fout)
                    ignore_cnt += 1
                elif any(tsent in trans_sent for tsent in trans):
                    print("  OK", file=fout)
                    match_cnt += 1  
                else:
                    print("  NOK", file=fout)

            print(file=fout)
        print("input={}, translated={}, matched={} exp_err={} ignored={} success=%{}".format(input_cnt,trans_cnt,match_cnt,experr_cnt,ignore_cnt,(match_cnt+experr_cnt+ignore_cnt)*100//input_cnt),file=fout)        


def interact(grm_fname, single_translation=False):
    parser = Parser("EN","TR")
    params = {}

    if grm_fname.endswith(".grmc"):
        start = timer()
        parser.load_grammar(grm_fname)
        end = timer()
        print("Grammar load time:",  timer_delta(start,end), "mics")
    else:
        start = timer()
        parser.parse_grammar(grm_fname)
        end = timer()    
        print("Grammar parse time:",  timer_delta(start,end), "mics")

        start = end
        parser.compile()
        end = timer()
        print("Compile time:",  timer_delta(start,end), "mics")

    print("Number of rules:", len(parser.rules))
    print("Number of states:", len({nstate for _,nstate in parser.dfa.items()}))
    print("Number of symbols:", len({symbol for (state,symbol),nstate in parser.dfa.items()}))
    print("Number of NonTerm symbols:", len(parser.ruledict))

    sent = input("Enter Sent> ")
    while sent:
        if sent == "%debug=1":
            print(parser.format_rules())
            logging.getLogger().setLevel(logging.DEBUG)
        elif sent == "%debug=0":
            logging.getLogger().setLevel(logging.CRITICAL)
        elif sent.startswith("%"):
            key,val = sent[1:].split("=")
            params[key] = int(val)
        else:
            trans_list = parser.trans_sent(sent, params.get("show_tree",0))
            if type(trans_list) == str:
                print(" ", trans_list)
            else:
                show_alternate = params.get("show_alternate",1)
                if show_alternate == 0:
                    print(" ", trans_list[0][0]) # print only least cost translation
                elif show_alternate == 1:
                    least_cost = trans_list[0][1]
                    for sent,cost in trans_list:
                        if cost != least_cost:
                            break
                        print(" ", sent)
                elif show_alternate == 2:
                    for sent,cost in trans_list:
                        print(" ", sent, cost)
        sent = input("Enter Sent> ")

def save(grm_fname):
    parser = Parser("EN","TR")

    if grm_fname.endswith(".grm"):
        grmc_fname = grm_fname[:-4] + ".grmc"
    else:
        grmc_fname = grm_fname + ".grmc"
        grm_fname = grm_fname + ".grm"

    start = timer()
    parser.parse_grammar(grm_fname,defines={"PARSE_DICT"})
    end = timer()    
    print("Grammar parse time:",  timer_delta(start,end), "mics")

    start = end
    parser.compile()
    end = timer()
    print("Compile time:",  timer_delta(start,end), "mics")

    print("Number of rules:", len(parser.rules))
    print("Number of states:", len({nstate for _,nstate in parser.dfa.items()}))
    print("Number of symbols:", len({symbol for (state,symbol),nstate in parser.dfa.items()}))
    print("Number of NonTerm symbols:", len(parser.ruledict))

    parser.save_grammar(grmc_fname)

if __name__ == "__main__":

    if len(sys.argv) == 3:
        if sys.argv[2] == "-i":
            interact(sys.argv[1])
        elif sys.argv[2] == "-s":
            os.chdir(os.path.join(os.path.dirname(__file__), 'grm'))
            save(sys.argv[1])
        else:
            trans_file(sys.argv[1], sys.argv[2])
    elif len(sys.argv) == 1:
        interact(os.path.join(os.path.dirname(__file__), 'grm', 'main.grmc'))
    else:
        print("USAGE1: python test_file.py <grammar_file> <input_file>")
        print("USAGE2: python test_grm.py <grammar_file> -i")
        print("USAGE3: python test_grm.py <grammar_file> -s")
