""" Recursive Descent Grammar Parser 

(c) 2018 by Mehmet Dolgun, m.dolgun@yahoo.com

Grammar Rules:
Rule ::= Head "->" Prod [ ":" Prod ] [ Feat ] [ "#" Comment ]
Prod ::= ( Terminal | NonTerminal [ "-" Suffix ] [ FParam ] )* [ "{" Cost "}" ] 
Feat ::= "[" [ Name "=" Value ( "," Name "=" Value )* ] "]"
FParam ::= "(" [ Name [ "=" Value ] ( "," Name [ "=" Value ] )* ")"
where 
Terminal ::= Id starting with upper case, excluding "-"
NonTerminal ::= Id not starting with upper case, optionally double-quoted
Name, Value ::= Id

"""
import re
from collections import namedtuple

class GrammarError(Exception):
    """ Raised when a grammar cannot be parsed """
    pass

empty_list = list()
empty_dict = dict()

Rule = namedtuple('Rule', 'head, left, right, feat, lparam, rparam, lcost, rcost')
#print(Rule._source)

def format_feat(fdict,par='[]'):
    if not fdict:
        if type(fdict)==dict: # empty dict
            return par
        return ""
    return par[0] + ",".join(["=".join(item) if item[1] else item[0] for item in sorted(fdict.items())]) + par[1]

def format_rule(self):
    return "%s -> %s {%d}: %s {%d} %s" % (
        self.head, 
        " ".join( ['"'+symbol+'"' if fparam is False else symbol+format_feat(fparam,'()') for symbol,fparam in zip(self.left,self.lparam)] ),
        self.lcost,
        " ".join( ['"'+symbol+'"' if fparam is False else str(symbol)+format_feat(fparam,'()') for symbol,fparam in zip(self.right,self.rparam)] ),
        self.rcost,
        format_feat(self.feat,'[]')
    )

Rule.format = format_rule

class Grammar:
    NONTERM = re.compile("[_A-Z][-_A-Za-z0-9]*'*")
    TERM = re.compile('".*"|[-\'a-zıüöçğşðþý][-\'A-Za-zıüöçğşðþý]*')
    FEAT = re.compile('\*?[a-z0-9_]*')
    INTEGER = re.compile('-?[1-9][0-9]*')
    def add_range(chars,start,end):
        for ch in range(ord(start),ord(end)+1):
            chars.add(chr(ch))
    word_chars = set('_-ıüöçğşðþý"\'') 
    add_range(word_chars,'A','Z')
    add_range(word_chars,'a','z')
    add_range(word_chars,'0','9')
   
    def __init__(self,s,line=0):
        self.s = s
        self.pos = 0
        self.line = line

    def get_rest(self,maxchars=20):
        return self.s[self.pos:self.pos+maxchars]

    def get_eof(self,ensure=True):
        self.skip_ws()
        if self.pos == len(self.s) or self.s[self.pos] == '#':
            return True
        if ensure:
            raise GrammarError("Line:%d Pos:%d EOF expected but found: %s..." % (self.line,self.pos,self.get_rest()))

    def get_token(self,token,ensure=True,skip_ws=True):
        if skip_ws:
            self.skip_ws()
        if self.s.startswith(token,self.pos):
            self.pos += len(token)
            return True
        if ensure:
            raise GrammarError("Line:%d Pos:%d '%s' expected but found: %s..." % (self.line,self.pos,token,self.get_rest()))

    def skip_ws(self):
        try:
            while self.s[self.pos] in " \t\r\n":
                self.pos += 1 
        except IndexError:
            pass

    def get_word(self,ensure=True,skip_ws=True):
        if skip_ws:
            self.skip_ws()
        start = self.pos
        try:
            while self.s[self.pos] in Grammar.word_chars:
                self.pos += 1 
        except IndexError:
            pass
        if start != self.pos:
            return self.s[start:self.pos]
        if ensure:
            raise GrammarError("Line:%d Pos:%d Word expected but found: %s..." % (self.line,self.pos,self.get_rest()))

    def get_symbol(self,ensure=True,skip_ws=True):
        word = self.get_word(ensure,skip_ws)
        if word:
            if Grammar.NONTERM.fullmatch(word):
                return word,0
            if Grammar.TERM.fullmatch(word):
                return word.strip('"'),1
            if ensure:
                raise GrammarError("Line:%d Pos:%d Symbol expected but found: '%s'" % (self.line,self.pos,word))
        return None,None

    def get_nonterm(self,ensure=True,skip_ws=True):
        word = self.get_word(ensure,skip_ws)
        if word:
            if Grammar.NONTERM.fullmatch(word):
                return word
            if ensure:
                raise GrammarError("Line:%d Pos:%d NonTerm expected but found: '%s'" % (self.line,self.pos,word))

    def get_feat(self,ensure=True,skip_ws=True):
        word = self.get_word(ensure,skip_ws)
        if word:
            if Grammar.FEAT.fullmatch(word):
                return word
            if ensure:
                raise GrammarError("Line:%d Pos:%d FeatId expected but found '%s'" % (self.line,self.pos,word))

    def get_integer(self,ensure=True,skip_ws=True):
        word = self.get_word(ensure,skip_ws)
        if word:
            if Grammar.INTEGER.fullmatch(word):
                return int(word)
            if ensure:
                raise GrammarError("Line:%d Pos:%d Integer expected but found '%s'" % (self.line,self.pos,word))

    def parse_rule(self,reverse=False):
        """ parses a rule and return an object of type Rule """
        if self.get_eof(False):
            return None

        head = self.get_nonterm()

        self.get_token('->')

        left,lparam,lcost = self.parse_prod()
        if self.get_token(':',False):
            right,rparam,rcost = self.parse_prod()
        else:
            right,rparam,rcost = empty_list,empty_list,0
        if self.get_token('[',False):
            feat = self.parse_feat()
        else:
            feat = empty_dict
        self.get_eof()

        if reverse:
            left,lparam,lcost,right,rparam,rcost = right,rparam,rcost,left,lparam,lcost
        
        # following cross-references right with left, removing referencing suffixes
        #  e.g.  VP -> give NP-prim NP-secn : NP-prim -yA NP-secn ver => VP -> give NP NP : 1 -yA 2 ver
        for idx,(symbol,param) in enumerate(zip(right,rparam)):
            if param is not False: # NonTerminal
                try:
                    right[idx] = left.index(symbol)
                except ValueError:
                    right[idx] = symbol.split('-')[0]

        for idx,(symbol,param) in enumerate(zip(left,lparam)):
            if param is not False: # NonTerminal
                left[idx] = symbol.split('-')[0]    

        return Rule(head,left,right,feat,lparam,rparam,lcost,rcost)

    def parse_prod(self):
        """ parses left or right grammar and builds references, returns tuple(symbol list,param list)  """
        prod = []
        param_list = []
        symbol,stype = self.get_symbol(False)
        while symbol:
            if stype == 0: # NonTerminal
                if self.get_token('(', False, skip_ws=False):
                    param = self.parse_fparam()
                else:
                    param = None
            else:
                param = False   
            prod.append(symbol)
            param_list.append(param)
            symbol,stype = self.get_symbol(False)
        if self.get_token('{',False):
            cost = self.get_integer()
            self.get_token('}')
        else:
            cost = 0

        return prod,param_list,cost

    def parse_feat(self):
        """ Parses feature list returns dict of name=value """
        name = self.get_feat(False)
        if not name and self.get_token(']',False): # empty list
            return empty_dict
        fdict = dict()
        self.get_token('=')
        value = self.get_feat()  
        fdict[name] = value

        while self.get_token(',', False):   
            name = self.get_feat()
            self.get_token('=')
            value = self.get_feat()  
            fdict[name] = value
        self.get_token(']')
        return fdict

    def parse_fparam(self):
        """ Parses feature parameter list returns dict of name=value or name=None """
        name = self.get_feat(False)
        if not name and self.get_token(')',False): # empty list
            return empty_dict
        fdict = dict()
        if self.get_token('=', False):
            value = self.get_feat()
            fdict[name] = value
        else:
            fdict[name] = None
        while self.get_token(',', False):   
            name = self.get_feat()
            if self.get_token('=', False):
                value = self.get_feat()
                fdict[name] = value
            else:
                fdict[name] = None
        self.get_token(')')
        return fdict

    def load_grammar(fname=None,reverse=False,text=None):
        """ loads a grammar file and parse it """
        if bool(fname) == bool(text):
            raise GrammarError("load_grammar: either fname or text should be provided")
        if text is None:
            with open(fname, "r") as f:
                return Grammar.parse_grammar(f,reverse)
        else:
            return Grammar.parse_grammar(text.split('\n'),reverse)
        

    def parse_grammar(iterator,reverse=False):
        rules = []
        rules.append(Grammar("S' -> S() : S()").parse_rule())
        line_no = 0
        process = True
        for s in iterator:
            line_no += 1
            if s.startswith('#'):
                if s.startswith('#ifdef'):
                    process = False
                elif s.startswith('#endif'):
                    process = True
                continue
            if not process:
                continue
            rule = Grammar(s,line_no).parse_rule()
            if rule is None: # empty/comment line
                continue
            rules.append(rule)
        return rules


def main():
    text = """
    VP -> Modal Ven-1 "isn't" -'s  : Ven-1(mode=pres,pers,numb) Tense() -iyor [mode=pres_perf] # a comment
    VP -> [pers=1] @ test
    VP -> : çalışıyor [pers=1]
    VP ->
    """
    line = 0
    for s in text.split('\n'):
        line += 1
        g = Grammar(s,line)
        print("Parsing: %s" % s)
        try:
            rule = g.parse_rule()
            if rule is None:
                continue
            #print(rule)
            print('    ',rule.format())
        except GrammarError as pe:
            print('    ',pe.args[0])

def fmain():
    rules = Grammar.load_grammar("test.grm")
    for rule in rules:
        print(rule.format())
if __name__ == "__main__":
    # execute only if run as a script
    fmain()

      
