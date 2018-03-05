import sys,logging
sys.path.append("../..")
from GLRParser import Parser, ParseError, GrammarError

logging.basicConfig(level=logging.DEBUG,filename="parser.log",filemode="w")

def test1():
    parser = Parser("EN","TR")
    parser.load_grammar("tenses.grm")
    parser.compile()
    parser.trans_file("tenses.in.txt","tenses.out.txt")

def test2():
    grammar = """
    S -> Subj AuxBe Not Ving : Subj Ving -Hyor Pers
    Subj -> i : ben
    AuxBe -> am
    Not -> not
    Not ->
    Ving -> going : git
    Pers -> -Hm
    """

    parser = Parser("EN","TR")
    parser.load_grammar(text=grammar)
    parser.compile()
    print(parser.trans_sent("i am going"))


test1()
