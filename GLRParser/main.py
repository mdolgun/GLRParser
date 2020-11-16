""" A GLR Parser for Natural Language Processing and Translation

(c) 2020 by Mehmet Dolgun, m.dolgun@yahoo.com

This file is defines a main program to test a grammar using a batch input file or interactively

Command Line Usage:

USAGE1:  python -m GLRParser.main <grammar_file> <input_file>
    e.g. python -m GLRParser.main main.grm main   
        * Loads and compiles the grammar file "main.grm"
        * Loads the input file "main.in.txt"
        * Translates each sentence in the input files and compares with the expected translation
        * Writes all translations and the results to the file "main.out.txt"
    Input file should consist of lines of the format: 
        <source_sentence> @ <translation> ("|" <alternate_translations>)* | "*"
        only-whitespace lines or lines starting with "#" are ignored
    e.g. a glass of water @ bir bardak su | bir su bardağı

USAGE2:  python -m GLRParser.main -i <grammar_file>
    e.g. python -m GLRParser.main -i main.grm
        * Loads and compiles the grammar file "main.grm"
        * Gets a sentence from the standard input
        * Translates the sentence and write translation to the standard out
        * Exits on empty input

USAGE3:  python -m GLRParser.main -s <grammar_file>
    e.g. python -m GLRParser.main -s main.grm
        * Loads and compiles the grammar file "main.grm"
        * Saves the compiled grammar "main.grmc"

OPTIONAL PARAMETERS:
    -g  Loads grammar files from the "grm" directory within the package
"""
import sys,logging,os
import os.path
from collections import defaultdict

if os.path.dirname(__file__) == os.getcwd(): # file is run directly from the source directory
    sys.path.append(os.path.join(os.path.dirname(__file__),".."))

from GLRParser.parser import Parser,ParseError,UnifyError,PostProcessError
from GLRParser.tree import *

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
            show_tree = params.get("show_tree",0)
            show_expr = params.get("show_expr",1)
            show_alternate = params.get("show_alternate",1)
            try:
                sent = parser.pre_processor(sent)
                parser.parse(sent)
                tree = parser.make_tree()
                if show_tree:
                    print(tree.pformat_ext())
                tree2 = parser.unify_tree(tree)
                if show_tree:
                    print(tree2.pformat_ext())
                tree3 = parser.trans_tree(tree2)
                if show_tree:
                    print(tree3.pformatr_ext())
                if show_expr:
                    opt_list,_cost = tree3.option_list()
                    results = []
                    combine_suffixes_lst(opt_list, 0, [], results)
                    post_process([results], parser.post_processor)
                    print_items_cost([results], sys.stdout); print()
                trans_dict = defaultdict(list)
                for sent,cost in tree3.enumx():
                    trans_dict[parser.post_processor(sent)].append(cost)
                trans_list = [(sent,min(costs)) for sent,costs in trans_dict.items()]
                trans_list.sort(key=lambda item:item[1])
                if show_alternate == 0: # print only first least cost translation
                    print(" ", trans_list[0][0])
                elif show_alternate == 1: # print all least cost translations
                    least_cost = trans_list[0][1]
                    for sent,cost in trans_list:
                        if cost != least_cost:
                            break
                        print(" ", sent)
                elif show_alternate == 2: # print all translations
                    for sent,cost in trans_list:
                        print(" ", sent, cost)
            except ParseError as pe:
                print("  ParseError: "+str(pe))
            except UnifyError as ue:
                print("UnifyError: "+str(ue))
            except PostProcessError as ppe:
                print("PostProcessError: "+str(ppe))
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

def print_usage():
        print("USAGE1: python -m GLRParser.main [-g] <grammar_file> <input_file>")
        print("USAGE2: python -m GLRParser.main [-g] -i <grammar_file>")
        print("USAGE3: python -m GLRParser.main [-g] -s <grammar_file>")

if __name__ == "__main__":
    import getopt
    optlist,args = getopt.getopt(sys.argv[1:],"gis")
    flags = {opt[0] for opt in optlist}
    if '-g' in flags:
        os.chdir(os.path.join(os.path.dirname(__file__), 'grm'))
    if '-i' in flags:
        if len(args) == 1:
            interact(args[0])
        else:
            print_usage()
    elif '-s' in flags:
        if len(args) == 1:
            save(args[0])
        else:
            print_usage()
    else:
        if len(args) == 0:
            interact(os.path.join(os.path.dirname(__file__), 'grm', 'main.grmc'))
        elif len(args) == 2:
            trans_file(args[0], args[1])
        else:
            print_usage()

