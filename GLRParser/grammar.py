""" Recursive Descent Grammar Parser 

(c) 2018 by Mehmet Dolgun, m.dolgun@yahoo.com

Source for parsing input grammar, defines classes GrammarError,Rule,Trie and Grammar

"""
import re, pickle

class GrammarError(Exception):
    """ Raised when a grammar cannot be parsed """
    pass

class FParam(dict):
    pass

empty_list = list()
empty_dict = dict()
empty_fparam = FParam()

class Rule:
    """ Definition of  a grammar rule """
    __slots__ = ('head', 'left', 'right', 'feat', 'checklist', 'lparam', 'rparam', 'cost', 'cut')

    def __init__(self, head, left=empty_list, right=empty_list, feat=empty_dict, checklist=empty_dict, lparam=empty_list, rparam=empty_list, cost=0, cut=None):
        self.head = head
        self.left = left
        self.right = right
        self.feat = feat
        self.checklist = checklist
        self.lparam = lparam
        self.rparam = rparam
        self.cost = cost
        self.cut = cut

    def format(self):
        return "%s -> %s : %s {%d} %s %s" % (
            self.head, 
            " ".join( '"'+symbol+'"' if fparam is False else symbol+format_fparam(fparam) for symbol,fparam in zip(self.left,self.lparam) ),
            " ".join( '"'+symbol+'"' if fparam is False else str(symbol)+format_fparam(fparam) for symbol,fparam in zip(self.right,self.rparam) ),
            self.cost,
            "!" if self.cut else "",
            format_feat(self.feat,self.checklist)
    )
    def __str__(self):
        return self.format()

    def __repr__(self):
        return self.format()

    def __eq__(self,other):
        return ((self.head, self.left, self.right, self.feat, self.checklist, self.lparam, self.rparam, self.cost, self.cut) == 
            (other.head, other.left, other.right, other.feat, other.checklist, other.lparam, other.rparam, other.cost, other.cut)) 

def format_fparam(fdict):
    if not fdict:
        if type(fdict)==dict: # empty dict
            return "()"
        return ""
    if fdict.param_type:
        param_type = fdict.param_type+","
    else:
        param_type = ""
    return "(" + param_type + ",".join("{}={}".format(item[0],item[1]) if item[1] is not None else item[0] for item in sorted(fdict.items())) + ")"

def format_feat(fdict,checklist=empty_dict):
    #if fdict is None:
    #    return ""
    checklist_out = ",".join("=".join(item) for item in checklist.items())
    feat_out = ",".join("=".join(item) if type(item[1])==str else item[0]+'=*' for item in sorted(fdict.items()))
    return "[" + ",".join(item for item in (checklist_out,feat_out) if item) + "]"

class Trie:
    """ Trie is  tree where each nodes are words (or characters). It is used as a dictionary 

    Note that it is advantageous over a hash dictionary that, any substring of input string can easily be looked up efficiently retrieving all valid phrases,
    which may also be prefix of another phase. e.g. root -> united(leaf) -> states(leaf) -> of -> america(leaf)
    """
    leaf = '$$$'
    
    def __init__(self):
        self.root = dict()
        
    def add(self,keyseq,val):
        curr_dict = self.root
        for key in keyseq:
            curr_dict = curr_dict.setdefault(key,dict())
        curr_dict.setdefault(self.leaf,[]).append(val)

    def search(self,keyseq):
        result = []
        curr_dict = self.root
        for idx,key in enumerate(keyseq):
            try:
                curr_dict = curr_dict[key]
                for val in curr_dict.get(self.leaf,[]):
                    result.append((idx+1,val))
            except KeyError:
                pass
        return result

    def list(self):
        lst = []
        yield from Trie.list_int(self.root,lst)

    def list_int(dic,lst):
        for key,val in dic.items():
            if key == Trie.leaf:
                yield "{} : {}".format(" ".join(lst),",".join(["{} -> {} {{{}}} {}".format(item.head," ".join(item.right),item.cost,format_feat(item.feat)) for item in val]))
                #print(lst,":",val)
            else:
                yield from Trie.list_int(val,lst+[key])


class Grammar:
    INTEGER = re.compile('-?[1-9][0-9]*') # 
    re_NONTERM = r"\$?[_A-Z][-_A-Za-z0-9$]*'*"
    re_FEAT_NAME = "[a-z0-9_]+"
    re_FPARAM_NAME = r"@?{}|@?\*".format(re_FEAT_NAME)
    re_TERM = r'''"([^"]*)"|(\$?[^|{:[_A-Z#!"][^|{:[#!\s]*)'''

    #re_FEAT_VALUE = r"\*{}|\*{}|{}".format(re_NONTERM, re_FEAT_NAME ,re_TERM)
    re_FEAT_VALUE = r"{}|\*{}|\*{}|[?!]?[-+]?{}".format(re_NONTERM, re_NONTERM, re_FEAT_NAME ,re_FEAT_NAME)
    re_SYMBOL = r'({}|\*{})|({})'.format(re_NONTERM, re_FEAT_NAME, re_TERM)

    SYMBOL = re.compile(re_SYMBOL)
    FEAT_NAME = re.compile(re_FEAT_NAME)
    FEAT_VALUE = re.compile(re_FEAT_VALUE)
    FPARAM_NAME = re.compile(re_FPARAM_NAME)
    TERM = re.compile(re_TERM)
    NONTERM = re.compile(re_NONTERM)

    def __init__(self,reverse=False,defines=None):
        self.reverse = reverse
        self.line_no = 0
        self.rules = []
        self.trie = Trie()
        self.macros = dict()
        self.forms = dict()
        self.defines = set() if defines is None else defines
        self.process = True
        self.if_stack = []  
        self.suff_dict = dict()
        self.auto_dict = False
        self.include_stack = []
        self.parse_rule("S' -> S() : S()")
        #self.suff_dict_names = dict()
        #self.suff_idxs = dict()
        #self.suff_dict_list = []
        
   
    def get_rest(self,maxchars=20):
        return self.buf[self.pos:self.pos+maxchars]

    def get_eof(self,ensure=True):
        self.skip_ws()
        if self.pos == len(self.buf) or self.buf[self.pos] == '#':
            return True
        if ensure:
            raise GrammarError("Line:%d Pos:%d EOF expected but found: %s..." % (self.line_no,self.pos,self.get_rest()))

    def get_token(self,token,ensure=True,skip_ws=True):
        if skip_ws:
            self.skip_ws()
        if self.buf.startswith(token,self.pos):
            self.pos += len(token)
            return True
        if ensure:
            raise GrammarError("Line:%d Pos:%d '%s' expected but found: %s..." % (self.line_no,self.pos,token,self.get_rest()))

    def get_char_list(self,char_list,ensure=True,skip_ws=True):
        if skip_ws:
            self.skip_ws()
        char = self.buf[self.pos]
        if char in char_list:
            self.pos += 1
            return char
        if ensure:
            raise GrammarError("Line:%d Pos:%d '%s' expected but found: %s..." % (self.line_no,self.pos,char_list,self.get_rest()))

    def get_token_list(self,token_list,ensure=True,skip_ws=True):
        if skip_ws:
            self.skip_ws()
        for token in token_list:
            if self.buf.startswith(token,self.pos):
                self.pos += len(token)
                return token
        if ensure:
            raise GrammarError("Line:%d Pos:%d '%s' expected but found: %s..." % (self.line_no,self.pos,token_list,self.get_rest()))

    def skip_ws(self):
        try:
            while self.buf[self.pos] in " \t\r\n":
                self.pos += 1 
        except IndexError:
            pass

    def get_symbol(self,ensure=True,skip_ws=True):
        if skip_ws:
            self.skip_ws()
        match = Grammar.SYMBOL.match(self.buf,self.pos)
        if match:
            self.pos = match.end()
            if match.group(1):
                return match.group(1),0
            if match.group(2):
                return match.group(2).strip('"'),1
        if ensure:
            raise GrammarError("Line:%d Pos:%d Symbol expected but found: %s" % (self.line_no,self.pos,self.get_rest()))
        return None,None

    def get_nonterm(self,ensure=True,skip_ws=True):
        symbol,stype = self.get_symbol(ensure,skip_ws)
        if stype == 0:
            return symbol
        if ensure:
            raise GrammarError("Line:%d Pos:%d NonTerm expected but found: '%s'" % (self.line_no,self.pos,symbol))

    def get_term(self,ensure=True,skip_ws=True):
        symbol,stype = self.get_symbol(ensure,skip_ws)
        if stype == 1:
            return symbol
        if ensure:
            raise GrammarError("Line:%d Pos:%d Term expected but found: '%s'" % (self.line_no,self.pos,symbol))

    def get_re(self,regexp,ensure=True,skip_ws=True):
        if skip_ws:
            self.skip_ws()
        match = regexp.match(self.buf,self.pos)
        if match:
            self.pos = match.end()
            return match.group()
        if ensure:
            raise GrammarError("Line:%d Pos:%d %s expected but found %s" % (self.line_no,self.pos,regexp,self.get_rest()))

    def get_integer(self,ensure=True,skip_ws=True):
        if skip_ws:
            self.skip_ws()
        match = Grammar.INTEGER.match(self.buf,self.pos)
        if match:
            self.pos = match.end()
            return int(match.group())
        if ensure:
            raise GrammarError("Line:%d Pos:%d FeatId expected but found %s" % (self.line_no,self.pos,self.get_rest()))

    def parse_rule(self,buf):
        """ parses a rule and return an object of type Rule """
        self.buf = buf
        self.pos = 0

        if self.get_eof(False):
            return

        macro_name,head = self.parse_head()

        self.get_token('->')

        llist = self.parse_prod()
        if self.get_token(':',False):
            rlist = self.parse_prod()
        else:
            rlist = [(empty_list,empty_list,0,None,None)]
        if self.get_token('[',False):
            feat,checklist = self.parse_feat_list()
        else:
            feat = empty_dict
            checklist = empty_dict
        self.get_eof()

        if self.reverse:
            llist,rlist = rlist,llist

        for left,lparam,lcost,lmacro,lcut in llist:
            term_only = self.auto_dict is not False and len(lparam)>0 and all(map(lambda x:x is False,lparam))

            for right,rparam,rcost,rmacro,rcut in rlist:      
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

                # TODO: if there are two alternatives and position of reference NT doesn't match it takes only first position (intelligent copy needed)
                for key,val in feat.items(): 
                    if val[0] == '*':
                        try:
                            feat[key] = left.index(val[1:])
                        except ValueError:
                            raise GrammarError("Line:%d No matching NonTerminal found for reference feature %s=%s" % (self.line_no,key,val))

                for idx,(symbol,param) in enumerate(zip(left,lparam)):
                    if param is not False: # NonTerminal
                        left[idx] = symbol.split('-')[0]
                if macro_name:
                    if not lmacro:
                        raise GrammarError("Line:%d No form substitution defined for macro %s" % (self.line_no,self.buf))
                    idx,word = lmacro
                    if word not in self.forms[macro_name]:
                        raise GrammarError("Line:%d No form defined for word '%s': %s" % (self.line_no,word,self.buf))
                    for _head,form in zip(head,self.forms[macro_name][word]):
                        for altform in form:
                            _left = left.copy()
                            _left[idx] = left[idx].replace('$'+word, altform)
                            if term_only:
                                self.trie.add(_left, Rule(_head,_left,right,feat,checklist,lparam,rparam,rcost,rcut) )
                                #!self.trie.add(left, Rule(head,left,lparam,[(right,rparam,feat,checklist,rcost)]) )
                            else:
                                self.rules.append( Rule(_head,_left,right,feat,checklist,lparam,rparam,rcost,rcut) )
                                #!self.rules.append( Rule(head,left,lparam,[(right,rparam,feat,checklist,rcost)]) )
                else:
                    if term_only:
                        self.trie.add(left, Rule(head,left,right,feat,checklist,lparam,rparam,rcost,rcut) )
                        #!self.trie.add(left, Rule(head,left,lparam,[(right,rparam,feat,checklist,rcost)]) )
                    else:
                        self.rules.append( Rule(head,left,right,feat,checklist,lparam,rparam,rcost,rcut) )
                        #!self.rules.append( Rule(head,left,lparam,[(right,rparam,feat,checklist,rcost)]) )

    def parse_head(self):
        if self.buf[self.pos] == '$':
            self.pos += 1
            macro = True
        else:
            macro = False
        symbol = self.get_nonterm(True,False)
        if macro:
            macro_name = symbol
            if symbol not in self.macros:
                raise GrammarError("Line:%d Macro %s not defined: %s" % (self.line_no,macro_name,self.buf))
            head = self.macros[symbol]
        else:
            macro_name = None
            head = symbol
        return macro_name,head
    
    def parse_alt(self):
        """ parses left or right grammar and builds references, returns tuple(symbol list,param list)  """
        prod = []
        param_list = []
        macro_var = None
        symbol,stype = self.get_symbol(False)
        idx = 0
        while symbol:
            if stype == 0: # NonTerminal
                if self.get_token('(', False, skip_ws=False):
                    param = self.parse_fparam_list()
                else:
                    param = None
            else:
                param = False
                pos = symbol.find('$')
                if pos != -1:
                    macro_var = (idx,symbol[pos+1:])
            prod.append(symbol)
            param_list.append(param)
            symbol,stype = self.get_symbol(False)
            idx += 1

        if self.get_token('{',False):
            cost = self.get_integer()
            self.get_token('}')
        else:
            cost = 0

        cut = self.get_token('!',False)

        return prod,param_list,cost,macro_var,cut

    def parse_prod(self):
        alts = [self.parse_alt()]
        while self.get_token('|',False):
            alts.append( self.parse_alt() )
        return alts

    def parse_feat(self):
        char = self.get_char_list("+-?!",False)
        if char:
            name = self.get_re(self.FEAT_NAME)
            value = char
        else:
            name = self.get_re(self.FEAT_NAME)
            self.get_token('=')
            value = self.get_re(self.FEAT_VALUE)
        return name,value

    def parse_fparam(self):
        char = self.get_char_list("+-",False)
        if char:
            name = self.get_re(self.FPARAM_NAME)
            value = char
        else:
            name = self.get_re(self.FPARAM_NAME)
            if self.get_token('=',ensure=False):
                value = self.get_re(self.FEAT_VALUE)
            else:
                value = None
        return name,value


    def parse_feat_list(self):
        """ Parses feature list returns dict of name=value """
        if self.get_token(']',False): # empty list
            return empty_dict,empty_dict
        fdict = dict()
        checklist = dict()
        name,value = self.parse_feat()
        if value.startswith("?") or value.startswith("!"):
            checklist[name] = value
        else:
            fdict[name] = value
        while self.get_token(',', False):   
            name,value = self.parse_feat()
            if value.startswith("?") or value.startswith("!"):
                checklist[name] = value
            else:
                fdict[name] = value
        self.get_token(']')
        return fdict,checklist

    def parse_fparam_list(self):
        """ Parses feature parameter list returns dict of name=value or name=None """
        if self.get_token(')',False): # empty list
            return empty_fparam
        fdict = FParam()
        fdict.param_type = self.get_token_list(["+,","-,"],False)
        if fdict.param_type:
            fdict.param_type = fdict.param_type[0]

        name,value = self.parse_fparam()
        fdict[name] = value
        while self.get_token(',', False):   
            name,value = self.parse_fparam()
            fdict[name] = value
        self.get_token(')')
        return fdict

    def load_grammar(fname=None,reverse=False,text=None,defines=None):
        """ loads a grammar file and parse it """
        if bool(fname) == bool(text):
            raise GrammarError("load_grammar: either fname or text should be provided")
        grammar = Grammar(reverse,defines)
        if text is None:
            grammar.fname = fname
            with open(fname, "r", encoding="utf-8") as f:
                grammar.parse_grammar(f)
                return grammar
        else:
            grammar.fname = ""
            grammar.parse_grammar(text.split('\n'))
            return grammar

    def parse_nonterm_list(self):
        items = []
        items.append(self.get_nonterm())
        while self.get_token(',',False):
            items.append(self.get_nonterm())
        return items

    def parse_term_list(self):
        items = []
        items.append(self.get_term())
        while self.get_token(',',False):
            items.append(self.get_term())
        return items

    def parse_macro(self):
        #""" %macro MacroName -> NonTerm (, NonTerm)* """
        #macro_name = self.get_nonterm()
        #self.get_token('->')
        #items = self.parse_nonterm_list()

        _,macro_name,items = self.buf.split()
        if macro_name in self.macros:
            raise GrammarError("Line:%d Macro already defined: %s" % (self.line_no,macro_name))
        self.macros[macro_name] = items.split(",")
        self.forms[macro_name] = dict()

    def parse_form(self):
        """ %form MacroName -> Term (, Term)* """
        #macro_name = self.get_nonterm()
        #self.get_token('->')

        _,macro_name,items = self.buf.split()
        if macro_name not in self.macros:
            raise GrammarError("Line:%d Macro not defined: %s" % (self.line_no,macro_name))
        cnt = len(self.macros[macro_name])
        #items = self.buf[self.pos:].split(",")
        items = items.split(",")
        if len(items) != cnt:
            raise GrammarError("Line:%d Form expecting %d items but found: %s" % (line_no,cnt,self.get_rest()))
        items = [[alt.strip() for alt in item.split("/")] for item in items]
        for alt in items[0]:
            self.forms[macro_name][alt] = items

    def parse_define(self):
        """ %define Token (, Token)* """
        items = self.parse_term_list()
        for item in items:
            self.defines.add(item)

    def parse_ifdef(self):
        """ %ifdef Token """
        item = self.get_term()
        self.if_stack.append(item in self.defines)
        self.process = all(self.if_stack)
        
    def parse_else(self):
        """ %else """
        self.if_stack[-1] = not self.if_stack[-1]
        self.process = all(self.if_stack)

    def parse_endif(self):
        """ %endif """
        self.if_stack.pop()
        self.process = all(self.if_stack)

    def include(self):
        """ %include "file name" """
        fname = self.get_term()
        self.include_stack.append({"fname":self.fname, "line_no":self.line_no, "auto_dict":self.auto_dict})
        with open(fname,"rt",encoding="utf-8") as f:
            self.parse_grammar(f)
        params = self.include_stack.pop()
        self.fname = params["fname"]
        self.line_no = params["line_no"]
        self.auto_dict = params["auto_dict"]

    def include_form(self):
        """ %include_form MacroName "file name" """
        macro_name = self.get_nonterm()
        fname = self.get_term()
        if macro_name not in self.macros:
            raise GrammarError("Line:%d Macro not defined: %s" % (self.line_no,macro_name))
        cnt = len(self.macros[macro_name])
        with open(fname,"rt",encoding="utf-8") as f:
            for line_no,line in enumerate(f):
                line = line.strip()
                if line and not line.startswith("#"):
                    items = line.split(",")
                    if len(items) != cnt:
                        raise GrammarError("File:%s Line:%d Form expecting %d items but found: %s" % (fname,line_no,cnt,line))
                    items = [[alt.strip() for alt in item.split("/")] for item in items]
                    for alt in items[0]:
                        self.forms[macro_name][alt] = items

    def save_macros(self):
        """ %save_macros "file name" """
        fname = self.get_term()
        with open(fname,"wb") as fout:
            pickle.dump(self.forms,fout)
    
    def load_macros(self):
        """ %save_macros "file name" """
        fname = self.get_term()
        with open(self,"rb") as fin:
            self.forms = pickle.load(fin)

    def save_dict(self):
        """ %save_dict "file name" """
        fname = self.get_term()
        with open(fname,"wb") as fout:
            pickle.dump(self.forms,fout)
    
    def load_dict(self):
        """ %load_dict "file name" """
        fname = self.get_term()
        with open(self,"rb") as fin:
            self.forms = pickle.load(fin)

    def parse_auto_dict(self):
        """%auto_dict false|true|all"""
        _,param = self.buf.split()
        self.auto_dict = {"false": False, "true": True, "all": "all"}.get(param)
        if self.auto_dict is None:
            raise GrammarError("Line:%d auto_dict unexpected parameter: %s" % (self.line_no,param))

    #def parse_suffix_macro(self):
    #    """ %suffix_macro MacroName -> term (, term)* """

    #    #macro_name = self.get_nonterm()
    #    #self.get_token('->')
    #    #items = self.parse_term_list()
    #    _,macro_name,_,items = self.buf.split()
    #    items = items.split(",")

    #    if macro_name in self.suff_dict_names:
    #        raise GrammarError("Line:%d Macro already defined: %s" % (self.line_no,macro_name))
    #    dict_idx = len(self.suff_dict_list)
    #    self.suff_dict_names[macro_name] = (dict_idx,len(items))
    #    self.suff_dict_list.append(dict())
    #    for idx,item in enumerate(items):
    #        self.suff_idxs[item] = (dict_idx,idx)


    #def parse_suffix_def(self):
    #    """ %suffix_def MacroName -> term (, term)* """

    #    #macro_name = self.get_nonterm()
    #    #self.get_token('->')
    #    #items = self.parse_term_list()
    #    _,macro_name,_,items = self.buf.split()
    #    items = items.split(",")

    #    if macro_name not in self.suff_dict_names:
    #        raise GrammarError("Line:%d Macro not defined: %s" % (self.line_no,macro_name))
    #    dict_idx,cnt = self.suff_dict_names[macro_name]
    #    #items = self.buf[self.pos:].split(",")
    #    if len(items) != cnt:
    #        raise GrammarError("Line:%d suffix_def expecting %d items but found: %s" % (self.line_no,cnt,self.buf))
    #    #items = [item.strip() for item in items]
    #    self.suff_dict_list[dict_idx][""] = items

    def parse_suffix(self):
        """ %suffix MacroName -> Term (, Term)* """

        #macro_name = self.get_nonterm()
        #self.get_token('->')
        #items = self.parse_term_list()
        _,key,val = self.buf.split()

        #if macro_name not in self.suff_dict_names:
        #    raise GrammarError("Line:%d Suffix Macro not defined: %s" % (self.line_no,macro_name))
        #dict_idx,cnt = self.suff_dict_names[macro_name]
        #items = self.buf[self.pos:].split(",")
        #if len(items) != cnt:
        #    raise GrammarError("Line:%d Suffix expecting %d items but found: %s" % (self.line_no,cnt,self.get_rest()))
        #items = [item.strip() for item in items]
        #self.suff_dict_list[dict_idx][items[0]] = items
        self.suff_dict[key] = val

    #def include_suffix(self):
    #    """ %include_suffix MacroName "file name" """
    #    macro_name = self.get_nonterm()
    #    fname = self.get_term()
    #    if macro_name not in self.suff_dict_names:
    #        raise GrammarError("Line:%d Suffix Macro not defined: %s" % (self.line_no,macro_name))
    #    dict_idx,cnt = self.suff_dict_names[macro_name]
    #    with open(fname,"rt") as f:
    #        for line_no,line in enumerate(f):
    #            line = line.strip()
    #            if line and not line.startswith("#"):
    #                items = line.split(",")
    #                if len(items) != cnt:
    #                    raise GrammarError("File:%s Line:%d Suffix Form expecting %d items but found: %s" % (fname,line_no,cnt,line))
    #                items = [item.strip() for item in items]
    #                self.suff_dict_list[dict_idx][items[0]] = items

    funcs = {
        "auto_dict": parse_auto_dict,
        "macro" : parse_macro,
        "form" : parse_form,
        "include_form" : include_form,
        "save_macros" : save_macros,
        "load_macros" : load_macros,
        "save_dict" : save_dict,
        "load_dict" : load_dict,
        "define" : parse_define,
        "ifdef" : parse_ifdef,
        "else"  : parse_else,
        "endif" : parse_endif,
        "include": include,
        #"suffix_macro" : parse_suffix_macro,
        #"suffix_def" : parse_suffix_def,
        "suffix" : parse_suffix,
        #"include_suffix": include_suffix,
#        "save_suffixes" : save_suffixes,
#        "load_suffixes" : load_suffixes,
    }
    def parse_grammar(self,iterator):
        for line in iterator:
            self.line_no += 1
            line = line.strip()
            if not line:
                continue
            if line.startswith('%'):
                parts = line[1:].split(maxsplit=1)
                if len(parts)==1:
                    command,rest=parts[0],""
                else:
                    command,rest = parts
                if not self.process and command not in {"ifdef","else","endif"}:
                    continue
                method = self.funcs.get(command)
                if method:
                    self.buf = line
                    self.pos = len(command)+2
                    method(self)
                else:
                    raise GrammarError("Line:%d Undefined command: %s" % (self.line_no,command))
            elif self.process:
                self.parse_rule(line)
      
