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

Rule = namedtuple('Rule', 'head, left, right, feat, lparam, rparam, cost')
#print(Rule._source)

def format_feat(fdict,par='[]'):
    if not fdict:
        if type(fdict)==dict: # empty dict
            return par
        return ""
    return par[0] + ",".join(["=".join(item) if item[1] else item[0] for item in sorted(fdict.items())]) + par[1]

def format_rule(self):
    return "%s -> %s : %s {%d} %s" % (
        self.head, 
        " ".join( ['"'+symbol+'"' if fparam is False else symbol+format_feat(fparam,'()') for symbol,fparam in zip(self.left,self.lparam)] ),
        " ".join( ['"'+symbol+'"' if fparam is False else str(symbol)+format_feat(fparam,'()') for symbol,fparam in zip(self.right,self.rparam)] ),
        self.cost,
        format_feat(self.feat,'[]')
    )

Rule.format = format_rule

class Grammar:
    SYMBOL = re.compile('''([_A-Z][-_A-Za-z0-9]*'*)|("[^"]*"|[-\'a-z0-9üöçğşðþýı][-\'A-Z0-9a-züöçğşıðþý+@^!]*)''')
    FEAT = re.compile('\*?[a-z0-9_]*')
    INTEGER = re.compile('-?[1-9][0-9]*')
   
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

    def get_char_list(self,char_list,ensure=True,skip_ws=True):
        if skip_ws:
            self.skip_ws()
        char = self.s[self.pos]
        if char in char_list:
            self.pos += 1
            return char
        if ensure:
            raise GrammarError("Line:%d Pos:%d '%s' expected but found: %s..." % (self.line,self.pos,char_list,self.get_rest()))

    def get_token_list(self,token_list,ensure=True,skip_ws=True):
        if skip_ws:
            self.skip_ws()
        for token in token_list:
            if self.s.startswith(token,self.pos):
                self.pos += len(token)
                return token
        if ensure:
            raise GrammarError("Line:%d Pos:%d '%s' expected but found: %s..." % (self.line,self.pos,token_list,self.get_rest()))

    def skip_ws(self):
        try:
            while self.s[self.pos] in " \t\r\n":
                self.pos += 1 
        except IndexError:
            pass

    def get_symbol(self,ensure=True,skip_ws=True):
        if skip_ws:
            self.skip_ws()
        match = Grammar.SYMBOL.match(self.s,self.pos)
        if match:
            self.pos = match.end()
            if match.group(1):
                return match.group(1),0
            if match.group(2):
                return match.group(2).strip('"'),1
        if ensure:
            raise GrammarError("Line:%d Pos:%d Symbol expected but found: %s" % (self.line,self.pos,self.get_rest()))
        return None,None

    def get_nonterm(self,ensure=True,skip_ws=True):
        symbol,stype = self.get_symbol(ensure,skip_ws)
        if stype == 0:
            return symbol
        if ensure:
            raise GrammarError("Line:%d Pos:%d NonTerm expected but found: '%s'" % (self.line,self.pos,symbol))

    def get_feat(self,ensure=True,skip_ws=True):
        if skip_ws:
            self.skip_ws()
        match = Grammar.FEAT.match(self.s,self.pos)
        if match:
            self.pos = match.end()
            return match.group()
        if ensure:
            raise GrammarError("Line:%d Pos:%d FeatId expected but found %s" % (self.line,self.pos,self.get_rest()))

    def get_integer(self,ensure=True,skip_ws=True):
        if skip_ws:
            self.skip_ws()
        match = Grammar.INTEGER.match(self.s,self.pos)
        if match:
            self.pos = match.end()
            return int(match.group())
        if ensure:
            raise GrammarError("Line:%d Pos:%d FeatId expected but found %s" % (self.line,self.pos,self.get_rest()))

    def parse_rule(self,reverse=False):
        """ parses a rule and return an object of type Rule """

        if self.get_eof(False):
            return []

        head = self.get_nonterm()

        self.get_token('->')

        llist = self.parse_prod()
        if self.get_token(':',False):
            rlist = self.parse_prod()
        else:
            rlist = [(empty_list,empty_list,0)]
        if self.get_token('[',False):
            feat = self.parse_feat_list()
        else:
            feat = empty_dict
        self.get_eof()

        if reverse:
            llist,rlist = rlist,llist

        rules = []
        for left,lparam,lcost in llist:
            for right,rparam,rcost in rlist:      
                # following cross-references right with left, removing referencing suffixes
                #  e.g.  VP -> give NP-prim NP-secn : NP-prim -yA NP-secn ver => VP -> give NP NP : 1 -yA 2 ver
                left = left.copy()
                right = right.copy()
                for idx,(symbol,param) in enumerate(zip(right,rparam)):
                    if param is not False: # NonTerminal
                        try:
                            right[idx] = left.index(symbol)
                        except ValueError:
                            right[idx] = symbol.split('-')[0]

                for idx,(symbol,param) in enumerate(zip(left,lparam)):
                    if param is not False: # NonTerminal
                        left[idx] = symbol.split('-')[0]    

                rules.append( Rule(head,left,right,feat,lparam,rparam,rcost) )
        return rules

    def parse_alt(self):
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

    def parse_prod(self):
        alts = [self.parse_alt()]
        while self.get_token('|',False):
            alts.append( self.parse_alt() )
        return alts

    def parse_feat(self,ensure_val=True):
        char = self.get_char_list("+-",False)
        if char:
            name = self.get_feat()
            value = char
        else:
            name = self.get_feat()
            if self.get_token('=',ensure=ensure_val):
                value = self.get_feat()
            else:
                value = None
        return name,value


    def parse_feat_list(self):
        """ Parses feature list returns dict of name=value """
        if self.get_token(']',False): # empty list
            return empty_dict
        fdict = dict()
        name,value = self.parse_feat()
        fdict[name] = value
        while self.get_token(',', False):   
            name,value = self.parse_feat()
            fdict[name] = value
        self.get_token(']')
        return fdict

    def parse_fparam(self):
        """ Parses feature parameter list returns dict of name=value or name=None """
        if self.get_token(')',False): # empty list
            return empty_dict
        fdict = dict()
        name,value = self.parse_feat(False)
        fdict[name] = value
        while self.get_token(',', False):   
            name,value = self.parse_feat(False)
            fdict[name] = value
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
        rules = Grammar("S' -> S() : S()").parse_rule()
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
            nrules = Grammar(s,line_no).parse_rule(reverse)
            rules.extend(nrules)
        return rules
      
