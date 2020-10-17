""" A GLR Parser for Natural Language Processing and Translation

(c) 2020 by Mehmet Dolgun, m.dolgun@yahoo.com

This file is defines a main program to test a grammar using a batch input file or interactively

Command Line Usage:

USAGE1: python test_file.py <grammar_file> <input_file>
    e.g. python test_file.py main main   
        * Loads and compiles the grammar file "main.grm"
        * Loads the input file "main.in.txt"
        * Translates each sentence in the input files and compares with the expected translation
        * Writes all translations and the results to the file "main.out.txt"
    Input file should consist of lines of the format: 
        <source_sentence> @ <translation> ("|" <alternate_translations>)* | "*"
        only-whitespace lines or lines starting with "#" are ignored
    e.g. a glass of water @ bir bardak su | bir su bardağı

USAGE2: python test_grm.py <grammar_file> -i
    e.g. python test_file.py main -i
        * Loads and compiles the grammar file "main.grm"
        * Gets a sentence from the standard input
        * Translates the sentence and write translation to the standard out
        * Exits on empty input
      
"""
import sys,logging,os

sys.path.append("../..")
from GLRParser import *
if sys.version_info >= (3, 7):
    from time import perf_counter_ns as timer
    def timer_delta(start,end,divider=1):
        return f'{(end-start)//(1000*divider):,}'
else:
    from time import perf_counter as timer
    def timer_delta(start,end,divider=1):
        return f'{int((end-start)*1000000/divider):,}'

#logging.basicConfig(level=logging.ERROR,filename="parser.log",filemode="w")

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
        start = timer()
        parser.load_grammar(f"{grm_fname}.grm")
        end = timer()
        print("Grammar load time:",  timer_delta(start,end),"mics")

        start = end
        parser.compile()
        end = timer()
        print("Compile time:",  timer_delta(start,end),"mics")

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
    start = timer()
    parser.load_grammar(f"{grm_fname}.grm")
    end = timer()
    print("Grammar load time:",  timer_delta(start,end),"mics")

    start = end
    parser.compile()
    end = timer()
    print("Compile time:",  timer_delta(start,end),"mics")

    print("Number of rules:", len(parser.rules))
    print("Number of states:", len({nstate for _,nstate in parser.dfa.items()}))
    print("Number of symbols:", len({symbol for (state,symbol),nstate in parser.dfa.items()}))
    print("Number of NonTerm symbols:", len(parser.ruledict))

    sent = input("Enter Sent> ")
    while sent:
        if sent == "%debug=1":
            print(parser.format_rules())
            logging.getLogger().setLevel(logging.DEBUG)
        else:
            trans_list = parser.trans_sent(sent)
            if type(trans_list) == str:
                print(trans_list)
            else:
                if single_translation:
                    print(trans_list[0][0]) # print only least cost translation
                else:
                    least_cost = trans_list[0][1]
                    for sent,cost in trans_list:
                        if cost != least_cost:
                            break
                        print(sent)
        sent = input("Enter Sent> ")

if len(sys.argv) == 3:
    if sys.argv[2] == "-i":
        interact(sys.argv[1])
    else:
        trans_file(sys.argv[1], sys.argv[2])
elif len(sys.argv) == 1:
    interact("main")
else:
    print("USAGE1: python test_file.py <grammar_file> <input_file>")
    print("USAGE2: python test_grm.py <grammar_file> -i")
