from GLRParser import Parser, ParseError, UnifyError, GrammarError

text = """
S -> NP(case=nom,numb,pers) VP NP(case=acc)
NP -> i     [case=nom,numb=sing,pers=1]
NP -> he    [case=nom,numb=sing,pers=3]
NP -> she   [case=nom,numb=sing,pers=3]
NP -> it    [numb=sing,pers=3]
NP -> we    [case=nom,numb=plur,pers=1]
NP -> you   [numb=plur,pers=2]
NP -> they  [case=nom,numb=plur,pers=3]
NP -> me    [case=acc,numb=sing,pers=1]
NP -> him   [case=acc,numb=sing,pers=3]
NP -> her   [case=acc,numb=sing,pers=3]
NP -> us    [case=acc,numb=plur,pers=1]
NP -> them  [case=acc,numb=plur,pers=3]

NP -> Det Noun  [pers=3]

Det -> this   [numb=sing]
Det -> these  [numb=plur]
Det -> a      [numb=sing]
Det -> two    [numb=plur]
Det -> the
Det ->

Noun -> man   [numb=sing]
Noun -> men   [numb=plur]

VP -> am  Ving  [numb=sing,pers=1]
VP -> is  Ving  [numb=sing,pers=3]
VP -> are Ving  [numb=plur]

VP -> was  Ving [numb=sing]
VP -> were Ving [numb=plur]

VP -> Ved
VP -> V         [numb=sing,pers=1]
VP -> Vs        [numb=sing,pers=3]
VP -> V         [numb=plur]

V    -> watch
Vs   -> watches
Ving -> watching
Ved  -> watched
"""

"""
parser = Parser()

parser.load_grammar(text=text)
parser.compile()
sents = ["i am watching her", "she is watching me", "these men are watching us", "me am watching you", "she is watching i", "two man is watching it",
         "a man watch us", "they watch us", "he watches the men", "he watches a men"]
for sent in sents:
    print(sent)
    try:
        parser.parse(sent)
        tree = parser.make_tree()
        tree2 = parser.unify_tree(tree)
        print(tree2.pformat_ext())
    except UnifyError as ue:
        print(ue)
    except ParseError as pe:
        print(pe)


parser = Parser()
parser.load_grammar(text=text)
parser.compile()
sents = ["i am watching them", "me am watching them", 
    "the men are watching her", "the man are watching her"]
for sent in sents:
    print(sent,':')
    try:
        parser.parse(sent)
        tree = parser.make_tree()
        tree2 = parser.unify_tree(tree)
        print(tree2.pformat_ext())
    except UnifyError as ue:
        print(ue,"\n")
    except ParseError as pe:
        print(pe,"\n")
"""
text =  """
S -> X(type=a,cnt) X(type=b,cnt)
X -> a  [cnt=1,type=a]
X -> aa [cnt=2,type=a]
X -> b  [cnt=1,type=b]
X -> bb [cnt=2,type=b]
"""

parser = Parser()
parser.load_grammar(text=text)
parser.compile()
try:
    parser.parse("a b")
    tree = parser.make_tree()
    tree2 = parser.unify_tree(tree)
    print(tree2.pformat_ext())
except UnifyError as ue:
    print(ue,"\n")
except ParseError as pe:
    print(pe,"\n")