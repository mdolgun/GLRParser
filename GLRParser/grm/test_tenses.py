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
    S -> Subj V                      : Subj V SimpTense         	[numb=sing,pers=1]
    S -> Subj V                      : Subj V SimpTense         	[numb=plur]
    Subj -> i [numb=sing,pers=1]
    V -> go : git
    SimpTense -> : -Ar Pers1	[tense=pres,neg=0]
    Pers1 -> : -YHm     [numb=sing,pers=1]
    Pers1 -> : -sHn     [numb=sing,pers=2]
    Pers1 -> :          [numb=sing,pers=3]
    Pers1 -> : -YHz     [numb=plur,pers=1]
    Pers1 -> : -sHnHz   [numb=plur,pers=2]
    Pers1 -> : -lAr     [numb=plur,pers=3]
    """

    parser = Parser("EN","TR")
    parser.load_grammar(text=grammar)
    parser.compile()
    parser.parse("i go")
    tree = parser.make_tree()
    print(tree.pformat_ext())
    utree = parser.unify_tree(tree)
    print(utree.pformat_ext())


test1()
