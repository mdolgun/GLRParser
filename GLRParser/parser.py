""" A GLR Parser for Natural Language Processing and Translation

(c) 2018 by Mehmet Dolgun, m.dolgun@yahoo.com

All functionality is provided by main class: Parser
The input grammar should be a list of rules in the form:
    NonTerminal "->" (SourceTerminal | NonTerminal)* [ ":" (DestTerminal|NonTerminal)* ] "#" Comment
empty lines and any characters after "#" are ignored
      
"""
import logging, re
from collections import defaultdict
from morpher import TurkishPostProcessor

empty_dict = dict()
empty_set = set()
empty_list = list()

class ParseError(Exception):
    """ Raised when a sentence cannot be parsed with current grammar """
    pass

class GrammarError(Exception):
    """ Raised when a grammar cannot be parsed """
    pass

class UnifyError(ParseError):
    """ Raised when a feature unification fails """
    pass

class EnglishPreProcessor:
    """ Pre-process a sentence, e.g. remove punctuation, normalize characters and spaces, and handles '(apostrophe) separation

    Rules:
    1. all punctuation symbols (except - and ') and whitespace is replaced with single space 
    2. all ' symbols except ending with t are seperated from root e.g "we're" -> "we 're", "house's" -> "house 's", "houses's" -> "houses '",  "isn't" -> "isn't"
    3. all letters are converted to lowercase

    """
    
    def __init__(self):
        self.regex = re.compile("[ ,.?:;()]+|(?='(?:[^t]|$))")
        
    def __call__(self,sent):
        return self.regex.sub(' ',sent).strip().lower()

class EnglishPostProcessor:
    """ Currently only handles combining apostrophe(')   e.g "we 're" -> "we're",  "house 's" -> "house's"
    todo: Regular inflections e.g "cry -ed" -> "cried", "cry -s" -> "cries" """
    
    def __init__(self):
        pass

    def __call__(self,sent):
        return sent.replace(" '", "'")
    

class TurkishPreProcessor:
    """ Curently only removes punctuations and normalizes spaces
    todo: Morphological parsing of Turkish words: e.g "uyumayacaGIm" -> "uyu -mA -yAcAk -yHm"  """
    
    def __init__(self):
        self.regex = re.compile("[ ,.?:;()]+")

    def __call__(self,sent):
        return self.regex.sub(' ',sent).strip()

class DummyProcessor:
    """ Default pre/post processor used in Parser """
    def __init__(self):
        self.regex = re.compile("[ ,.?:;()]+")
        
    def __call__(self,sent):
        return self.regex.sub(' ',sent).strip()  

class Parser:
    """ A GLR Parser for Natural Language Processing and Translation

		see main() for sample usage

        internal data:
            rules : list of rules as tuples (head,body,trans,feat) for a rule "head -> body : trans [feat]"
            ruledict : maps NT -> list of rulenos in "rules"
            nullable : set of nullable NTs, an NT is nullable if it can produce directly or indirectly an empty string
            dfa : Deterministic Finite Automaton for state transitions, where dfa[state,symbol] -> nextstate
            reduce : maps a state to a list of reductions  reduce[state] -> [(ruleno,rulepos)*]
            ereduce : maps a state to a list of empty reductions  ereduce[state] -> [(ruleno,rulepos)*]
    """

    def __init__(self,pre_processor=DummyProcessor(),post_processor=DummyProcessor(),reverse=False):
        """ initializes parser with pre_processor and post_processor, which should be callable, reverse reverses(i.e. swaps) the input/output grammars """
        self.pre_processor = pre_processor
        self.post_processor = post_processor
        self.reverse = reverse

        
    def closure(self,stateset):
        """ modifies parameter to add e-closure to existing set of states

        self.rules: [ rule(head,body[symbol*],trans) ]
        self.ruledict: { nt:{ruleno*} }
        """

        todo = list(stateset)
        # we use both list for iteration and set for membership check
        # for iteration we use set as FIFO, for membership check we use set for O(1) complexity
        for ruleno,rulepos in todo:
            try:
                symbol = self.rules[ruleno][1][rulepos]
                for nextno in self.ruledict.get(symbol,set()):
                    nextstate = (nextno,0)
                    if nextstate not in stateset: 
                        stateset.add(nextstate)
                        todo.append(nextstate)
                """
                while symbol in nullable:
                    rulepos += 1
                    nextstate = (ruleno,rulepos)
                    if nextstate not in stateset: 
                        stateset.add(nextstate)
                        todo.append(nextstate)              
                    symbol = rules[ruleno][1][rulepos]
                """
            except IndexError: # there is no more symbols in the rule (i.e. A->x.)
                pass

    def format_fdict(fdict):
        return ",".join(["=".join(item) for item in fdict.items()])

    def format_fset(fset):
        return ",".join(fset)

    def format_fparam(fparam):
        if fparam is None:
            return ""
        return "[" + ",".join((Parser.format_fdict(fparam[0]),Parser.format_fset(fparam[1]))) + "]"
           
    def format_rules(self):
        frules = []
        for head,src,dst,(fdict,srcflist,dstflist) in self.rules:
            """            logging.debug("src=%s", src);
            logging.debug("dst=%s", dst);
            logging.debug("srcflist=%s", srcflist);
            logging.debug("dstflist=%s", dstflist); """
            src = [symbol+Parser.format_fparam(fparam) for symbol,fparam in zip(src,srcflist)]
            dst = [str(symbol)+Parser.format_fparam(fparam) for symbol,fparam in zip(dst,dstflist)]
            """
            logging.debug("src2=%s", src);
            logging.debug("dst2=%s", dst);
            """
            frules.append("{} -> {} : {} [{}]".format(
                head,
                " ".join(src),
                " ".join(dst),
                Parser.format_fdict(fdict)
            ))
        return "\n".join(frules)
         
    def get_items(self,stateset):
        """ get string repr of "items" in state set in dotted fomat  e.g "{ S -> NP . VP ; VP -> . V  ; VP -> . V NP }" """
        slist = ["{"]
        for ruleno,rulepos in stateset:
            slist.append("{} --> {} . {}".format(self.rules[ruleno][0], " ".join(self.rules[ruleno][1][0:rulepos]), " ".join(self.rules[ruleno][1][rulepos:])))
        slist.append("}")
        return " , ".join(slist)

    def get_item(self,ruleno,rulepos):
        return "{} --> {} . {}".format(self.rules[ruleno][0], " ".join(self.rules[ruleno][1][0:rulepos]), " ".join(self.rules[ruleno][1][rulepos:]))    

    def compile(self):
        """ compile rule list "rules" to a DFA

        produces dfa, reduce and ereduce from rules
        """

        rules = self.rules
        ruledict = defaultdict(list)
        dfa = dict()
        reduce = defaultdict(set)
        ereduce = defaultdict(set)
        
        self.ruledict = ruledict
        self.dfa = dfa
        self.reduce = reduce
        self.ereduce = ereduce
        
        for ruleno,rule in enumerate(rules):
            ruledict[rule[0]].append(ruleno)

        # todo: more efficient algorithm for large grammars
        nullable = {rule[0] for rule in rules if len(rule[1])==0}  # empty productions
        flag = bool(nullable)
        while flag:
            flag = False
            for rule in rules:
                if all(map(lambda x:x in nullable,rule[1])): # all of symbols in RHS is nullable
                    if rule[0] not in nullable:
                        nullable.add(rule[0])
                        flag = True
            
        logging.info("nullable=%s", nullable)
        self.nullable = nullable
        
        statedict = dict() # maps set of nfa states to a single dfa state
        stateset = {(0,0)}
        self.closure(stateset)
        statedict[frozenset(stateset)] = 0
        states = [stateset] # list of nfa state set, also used to map dfa state to nfa state set
        todo = [0]
        for stateno in todo:
            tempdict = defaultdict(set) # maps symbol to set of next states
            for ruleno,rulepos in states[stateno]:          
                try:
                    symbol = rules[ruleno][1][rulepos] # get next symbol after dot (i.e. A->x.By)
                    tempdict[symbol].add((ruleno,rulepos+1))
                except IndexError: # there is no more symbols in the rule (i.e. A->x.)
                    pass
            for symbol,nextstateset in tempdict.items():
                self.closure(nextstateset)
                f = frozenset(nextstateset)
                nextstateno = statedict.get(f,-1)
                if nextstateno == -1:
                    nextstateno = len(states)
                    statedict[f] = nextstateno
                    states.append(nextstateset)
                    todo.append(nextstateno)
                dfa[stateno,symbol] = nextstateno
        for idx,stateset in enumerate(states):
            for ruleno,rulepos in stateset:
                body = rules[ruleno][1]
                if all(map(lambda x:x in nullable,body[rulepos:])): # if all remaining items are nullable
                    if rulepos == 0: # empty or nullable rule
                        ereduce[idx].add((ruleno,rulepos))                   
                    else:
                        reduce[idx].add((ruleno,rulepos))
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            for stateno,stateset in enumerate(states):
                logging.debug("%s : %s REDUCE: %s EREDUCE: %s", stateno, self.get_items(stateset), self.get_items(reduce.get(stateno,set())), self.get_items(ereduce.get(stateno,set())))
   

    def parse_feat(flist,param=False):
        """ parses a feature list and/or feature setof the form: (name ["=" val] )* "]"
        if param=True then returns flist,fset pair, otherwise return flist """

        flist = flist.split("]")
        if len(flist)==1:
            raise GrammarError("] expected")
        if param:
            fset = set()
        fdict = dict()
        for feat in flist[0].split(","):
            feat = feat.split("=")
            if len(feat)==1:
                if not param:
                    raise GrammarError("= expected")
                fset.add(feat[0])
            else:
                fdict[feat[0]]=feat[1]
        if not fdict:
            fdict = empty_dict
        if param:
            if not fset:
                fset = empty_set
            return fdict,fset
        else:
            return fdict     
        
    def split_grammar(self,iterator,reverse=False):
        """ get a list of grammar rules from iterator, splits and transforms it into list "rules"

        e.g. each rule S -> A B c : d B A becomes [S, [A, B, c], [d, 1, 0]],  where A,B is Non-Terminal c,d is Terminal
        todo: write a full parser with error detection
        """

        rules = [ ( "S'", ["S"], [0], (empty_dict,[None],[None]) ) ]
        for rule in iterator:
            rule = rule.split("#")
            rule = rule[0].strip()
            if not rule: # skip blank rules
                continue
            rule = rule.split("->")
            if len(rule)!=2:
                raise GrammarError("Invalid Grammar Rule", rule)
            body = rule[1].split(":")
            if reverse:
                if len(body)==2:
                    body[0],body[1] = body[1],body[0]
                else:
                    body.append(body[0])
                    body[0] = body[1]
            src = [] # e.g NP and NP
            src2 = [] # e.g NP-1 and NP-2
            srcflist = []
            dstflist = []
            fdict = empty_dict
            for symbol in body[0].split(" "):
                if not symbol: continue
                
                param = None
                symbol = symbol.split("[")
                if len(symbol)==2:
                    if symbol[0]:
                        param = Parser.parse_feat(symbol[1],True) 
                    else:
                        fdict = Parser.parse_feat(symbol[1]) # todo: error check for correct position
                        continue
                symbol = symbol[0]

                sparts = symbol.split("-")
                src.append(sparts[0])
                src2.append(symbol)
                srcflist.append(param)
            
            dst = []
            if len(body)==2: # there is a translation        
                for symbol in body[1].split(" "):
                    if not symbol: continue
                    
                    param = None
                    symbol = symbol.split("[")
                    if len(symbol)==2:
                        if symbol[0]:
                            param = Parser.parse_feat(symbol[1],True) 
                        else:
                            fdict = Parser.parse_feat(symbol[1]) # todo: error check for correct position
                            continue
                        
                    symbol = symbol[0]
                    try:                   
                        dst.append(src2.index(symbol))
                       
                    except ValueError:
                        dst.append(symbol)
                    dstflist.append(param)
            rules.append((rule[0].strip(), src, dst, (fdict,srcflist,dstflist)))
            
        self.rules = rules
        if logging.getLogger().isEnabledFor(logging.INFO):
            logging.info("rules=%s",self.format_rules())

    def load_grammar(self,filename,reverse=False):
        """ loads a grammar file and parse it """
        with open(filename, "r") as f:
            self.split_grammar(f,reverse)

    def get_prod(tree):
        """ tree = [head, ruleno, symbol*]

        return string representation in the form "head ruleno(sub1 sub2...)
        """
        if type(tree) == str: # if a terminal node
            return tree
        return tree[0] + str(tree[1]) + "(" + " ".join([Parser.get_tree(sub) for sub in tree[2:]]) + ")"
  
    def get_tree(tree):
        """ tree = [alt*] list of alternative for a production

        return string representation in the form "alt1|alt2..."
        """
        if type(tree) == str:
            return tree
        return "|".join([Parser.get_prod(alt) for alt in tree])

    def xlate_prod(self,tree):
        # tree = [head, ruleno, symbol*]
        # return translated string for the rule[ruleno]
        if type(tree) == str: # if a terminal node, normally it shouldn't come here
            return tree
        trans = []
        for item in self.rules[tree[1]][2]:
            if type(item)==str:
                trans.append(item)
            else:
                trans.append(self.xlate_tree(tree[item+2]))
        return " ".join(trans)
  
    def xlate_tree(self,tree):
        # tree = [alt*] list of alternative for a production
        # returns string of the form "(alt1|alt2...)" or "alt1" for single alternative
        if len(tree)==1:
            return self.xlate_prod(tree[0])
        else:
            return "(" + "|".join([self.xlate_prod(alt) for alt in tree]) + ")"

    def unify(dst,param,src):
        """ unification of "src" features into "dst" features, using filtering of "param", if unification fails raises UnifyError

        if param is None, src is directly unified into dst
        otherwise param contains a pre-condition dict and a filter set,
        src is checked against pre-condition dict and then filtered with filter set and unified into dst

        """
        if param is None:
            keys = src.keys()
        else:
            pdict,pset = param
            for key in pdict.keys() & src.keys():
                if src[key] != pdict[key]:
                    raise UnifyError(key, src[key], pdict[key])
            keys = pset & src.keys()

        for key in keys & dst.keys():
            if  src[key] != dst[key]:
                raise UnifyError(key, src[key], dst[key])

        newkeys = keys - dst.keys()
        if newkeys:
            dst = dst.copy()
            for key in newkeys:
                dst[key] = src[key]
        return dst
    
    def unify_prod(self,prod):
        fdict,srcflist,_ = self.rules[prod[1]][3]
        stack = [(fdict,[])]
        for item,param in zip(prod[2],srcflist):
            if type(item)==str:
                for fdict,seq in stack:
                    seq.append(item)
            else:
                nstack = []
                for fdict,seq in stack:
                    nkeys = []
                    nvals = []
                    for sub in self.unify_tree(item):                    
                        try:
                            _fdict = Parser.unify(fdict,param,sub[4])
                            try:
                                idx = nkeys.index(_fdict)
                                nvals[idx].append(sub) 
                            except ValueError:
                                nkeys.append(_fdict)
                                nvals.append([sub])
                        except UnifyError as ue:
                            pass
                    for key,val in zip(nkeys,nvals):
                        nstack.append((key,seq+[val]))
                stack = nstack
                if not stack:
                    raise UnifyError("Empty result")
        ntree = []
        for fdict,seq in stack:
            ntree.append([prod[0],prod[1],seq,prod[3],fdict])
        return ntree

    def unify_tree(self,tree):
        ntree = []
        for prod in tree:
            try:
                ntree += self.unify_prod(prod)            
            except UnifyError as ue:
                pass
        if not ntree:
            raise UnifyError("Empty result")
        return ntree

    def make_trans_tree(self,symbol,feat,fparam):
        """ generate a tree for dst-only non-terminal tree """
        ntree = []
        for ruleno in self.ruledict[symbol]:
            rule = self.rules[ruleno] # (head,src,dst,(feat,srcparamlist,dstparamlist))
            try:
                fdict = Parser.unify(feat,fparam,rule[3][0])
                logging.debug("make_trans_tree: %s unify(%s,%s,%s)->%s", symbol, Parser.format_fdict(feat), Parser.format_fparam(fparam), Parser.format_fdict(rule[3][0]), Parser.format_fdict(fdict))
                sub = []
                for item,param in zip(rule[2],rule[3][2]):
                    assert type(item) != int
                    if item[0].isupper():
                        sub.append( self.make_trans_tree(item,fdict,param) )
                    else:
                        sub.append(item)
                ntree.append([symbol,ruleno,[],sub,fdict]) # [head, ruleno, [symbol*], [tsymbol*], featdict]
            except UnifyError:
                pass
        if not ntree:
            raise UnifyError("empty make_trans_tree")
        return ntree
                   
    def trans_prod(self,tree,feat,fparam):
        # in  = [head, ruleno, [symbol*], None, featdict]
        # out = [head, ruleno, [symbol*], [tsymbol*], featdict]
        fdict = Parser.unify(tree[4],fparam,feat)
        logging.debug("trans_prod: %s unify(%s,%s,%s)->%s", tree[0], Parser.format_fdict(tree[4]), Parser.format_fparam(fparam), Parser.format_fdict(feat), Parser.format_fdict(fdict))                
        trans = []
        rule = self.rules[tree[1]]
        for item,param in zip(rule[2],rule[3][2]):
            if type(item)==str:
                if item[0].isupper(): # dst-only NT
                    trans.append( self.make_trans_tree(item,fdict,param) ) 
                else:
                    trans.append(item)
            else:
                trans.append(self.trans_tree(tree[2][item],fdict,param))
        if tree[3]:
            logger.info("trans  already exists OLD: %s NEW: %s ", tree[3], trans)
        tree[3] = trans
        return tree
  
    def trans_tree(self,tree,feat=empty_dict,fparam=None):
        # tree = [alt*] list of alternative for a production
        # returns [talt*] list of alternative translations for a production
        for alt in tree:
            self.trans_prod(alt,feat,fparam)
        return tree
        #return [self.trans_prod(alt) for alt in tree]

         
    def pformat_tree(tree,ttype=2,indent=""):
        """ pretty format (multiple lines with identationa) a tree 
        tree = [prod*] list of alternative productions """
        if type(tree) == str:
            return indent + tree
        def pformat_prod(prod,ttype,indent):
            """ prod = [head, ruleno, srcsymbol*, dstsymbol*, feats]  """
            if type(prod) == str:
                return indent + prod
            if not prod[ttype]: # empty production
                return indent + prod[0] + "[" + Parser.format_fdict(prod[4]) + "]()"
            else:
                return indent + prod[0] + "[" + Parser.format_fdict(prod[4]) + "](\n"+ "\n".join([Parser.pformat_tree(sub, ttype, indent + "+---") for sub in prod[ttype]]) + "\n" + indent + ")"
        return ("\n"+ indent + "|\n").join([pformat_prod(prod,ttype,indent) for prod in tree])

    def format_edge_item(alts):
        """ format an edge item to str (used internally for logging/debugging) """
        return " ".join(["{2}({0},{1};{3},{4})".format(*alt) for alt in alts[1:]])
      
    def format_edge(self,edge):
        """ format an edge into str (used internally for logging/debugging) """
        if edge not in self.edges:
            return "{2}({0},{1};{3},{4}) -> None".format(*edge)
        return  "{2}({0},{1};{3},{4}) -> ".format(*edge) + " | ".join( [ " ".join(["{2}({0},{1};{3},{4})".format(*alt) for alt in alts[1:]]) for alts in self.edges[edge]] )       
    
    def gen_prod(prod):
        """ a generator for producing all alternative translations of a production (recursively calling/called by gen_tree) """
        if not prod:
            yield ""
            return
        for first in Parser.gen_tree(prod[0]):
            for rest in Parser.gen_prod(prod[1:]):
                if first and rest:
                    yield first + " " + rest
                else:
                    yield first or rest
          
    def gen_tree(tree):
        """ a generator for producing all alternative translations of a tree """
        if type(tree) != list:
            yield tree
            return
        for alt in tree:
            yield from Parser.gen_prod(alt[3])  
  
    def print_parse_tables(self):
        indent = 7
        space = " "*indent
        for pos,token in enumerate(self.instr):
            print(str(pos).rjust(2,"-"),token.center(indent-2,"-"),sep="",end="")
        print()
        for (epos,estate,symbol),startset in sorted(self.nodes.items()):
            for spos,sstate in startset:
                print(space*spos, str(sstate).rjust(2), symbol.center((epos-spos)*indent-2,"="), str(estate).rjust(2,"="), " ", self.format_edge((spos,sstate,symbol,epos,estate)), sep="")
 
    def make_tree(self,edge=None):
        """ generates a tree (which is a recursive list of lists) from edges
        
        tree: [alt*] alt: [head,ruleno,[sub*],[trans*],[feat*]]
        """

        if edge is None:
            edge = self.top_edge
        if edge not in self.edges:
            return edge[2]
        alts = self.edges[edge]
        talt = []
        for alt in alts:
            rule = self.rules[alt[0]] 
            t = [edge[2],alt[0]] # head,ruleno
            t.append([self.make_tree(alt_edge) for alt_edge in alt[1:]])
            t.append([]) # place-holder for translation
            t.append(rule[3][0]) # place-holder for features
            talt.append(t)
        return talt;

       
           
    def print_dfa(self):
        """ prints dfa, reduce and e-reduce in a tabular format """
        width = 5
        symbols = sorted({symbol for (state,symbol),nstate in self.dfa.items()})
        states = {nstate for (state,symbol),nstate in self.dfa.items()}
        states.add(0)
        print("".rjust(width),",",end="")
        for symbol in symbols:
            print(symbol.rjust(width),",",end="")
        print("$")
        for state in states:
            print(str(state).rjust(width),",",end="")
            for symbol in symbols:
                print(str(self.dfa.get((state,symbol),"")).rjust(width),",",end="")
            print(self.reduce.get(state,""),self.ereduce.get(state,""))

    def parse_feat(flist,param=False):
        """ if param=False, parses a feature list: (feat"="val)*"]", else parses a parameter list: (param["="val])*"]"  """
        flist = flist.split("]")
        if len(flist)==1:
            raise GrammarError("] expected")
        if param:
            fset = set()
        fdict = dict()
        for feat in flist[0].split(","):
            feat = feat.split("=")
            if len(feat)==1:
                if not param:
                    raise GrammarError("= expected")
                fset.add(feat[0])
            else:
                fdict[feat[0]]=feat[1]
        if not fdict:
            fdict = empty_dict
        if param:
            if not fset:
                fset = empty_set
            return fdict,fset
        else:
            return fdict

    def parse(self,instr):
        """ parses input string using current grammar, throwing ParseError if parsing fails, the parse tree can be later retrieved from "edges" """
        
        dfa = self.dfa
        reduce = self.reduce
        ereduce = self.ereduce
        logging.info("input=%s", instr)

        instr = instr.split(" ")
        instr.append("$")
        inlen = len(instr)
        nodes = defaultdict(set) # maps (pos,state,symbol) to set of (oldpos,oldstate) (i.e adds an arc from (pos,state) to (oldpos,oldstate) labeled with symbol)
        edges = defaultdict(list) # maps an edge to sub-edges of a production e.g. (p0,s0,S,p2,s2') -> [ (p0,s0,NP,p1,s1), (p1,s1,VP,p2,s2) ] where s0,S->s2'
        fstate = dfa[0,"S"]
        
        self.nodes = nodes
        self.edges = edges
        self.instr = instr
        self.top_edge = (0,0,"S",inlen-1,fstate)

        active = {0}
        rset = set()
        
        for pos in range(inlen):
            token = instr[pos]         

            logging.debug("eset=%s rset=%s", active, rset)

            rlist = list(rset)

            for edge in rlist: # for each work item (start_position, start_state, edge_symbol, end_position, end_state)
                spos,sstate,esymbol,epos,estate = edge
                logging.debug("Checking Work Item: %s  All: %s", edge, rlist)
                for ruleno,rulepos in reduce.get(estate,set()): # find reducible items for end_state
                    head,body = self.rules[ruleno][0:2]
                    logging.debug("Reducing %s ", self.get_item(ruleno,rulepos))
                    ptree = [edge]
                        
                    state = estate
                    for symbol in body[rulepos:]: # iterate and append all right nulled symbols to ptree
                        nstate = dfa.get((state,symbol),-1)
                        ptree.append((epos,state,symbol,epos,nstate))
                        state = nstate
                        
                    stack = [(spos,sstate,ptree)]
                    if esymbol != body[rulepos-1]:
                        logging.warning("***MISMATCH*** esymbol=",esymbol,"lsymbol=",body[rulepos-1])
                    if rulepos >=2:
                        for symbol in body[rulepos-2::-1]:
                            nstack = []
                            for ppos,pstate,ptree in stack: 
                                for xpos,xstate in nodes[ppos,pstate,symbol]:
                                    nstack.append((xpos,xstate,[(xpos,xstate,symbol,ppos,pstate)]+ptree))
                                    
                            stack = nstack
                    for ppos,pstate,ptree in stack:                      
                        nstate = self.dfa.get((pstate,head),-1)
                        logging.debug("REDUCE %s , %s -> %s", pstate, head, nstate)
                        if nstate != -1:
                            active.add(nstate)
                            nodes[pos,nstate,head].add((ppos,pstate))
                            nedge = (ppos,pstate,head,pos,nstate) 
                            if nedge not in edges:
                                rlist.append(nedge)
                            ptree = [ruleno] + ptree
                            logging.debug("appending edge %s to %s", Parser.format_edge_item(ptree), self.format_edge(nedge))
                            edges[nedge].append(ptree)

            for state in active:
                for ruleno,rulepos in ereduce.get(state,set()):
                    logging.debug("e-Reducing %s", self.get_item(ruleno,rulepos))
                    head,body = self.rules[ruleno][0:2]
                    ptree = [ruleno]
                    estate = state
                    for symbol in body[rulepos:]:
                        nstate = dfa.get((estate,symbol),-1)
                        ptree.append((pos,state,symbol,pos,nstate))
                        estate = nstate
                    nstate = dfa.get((state,head),-1)
                    logging.debug("EREDUCE %s , %s -> %s", state, head, nstate)
                    if nstate!= -1:
                        edges[pos,state,head,pos,nstate].append(ptree)
      
            logging.debug("active=%s input= %s", active, token)
            if token == "$":
                if fstate in active:
                    logging.info("Parse successful")
                else:
                    logging.error("Parse not possible")
                    raise ParseError("Parse not possible")
            else:
                if not active:
                    logging.error("not active, %s",active)
                    raise ParseError("Cannot shift", " ".join(instr[0:pos]), "^", " ".join(instr[pos:]))
                rset = set()
                nactive = set()
                for state in active:
                    nstate = dfa.get((state,token),-1)
                    #print(state,",",token,"->",nstate)
                    if nstate != -1:
                        
                        logging.debug("add nodes[%s] = %s",(pos+1,nstate,token),(pos,state)) 
                        nodes[pos+1,nstate,token].add((pos,state))
                        logging.debug("shift %s = %s", (pos+1,nstate,token,pos,state),token)
                    
                        rset.add((pos,state,token,pos+1,nstate))
                        nactive.add(nstate)
                active = nactive

    def trans_sent(self,sent):
        try:
            sent = self.pre_processor(sent)
            self.parse(sent)
            tree = self.make_tree()
            tree2 = self.unify_tree(tree)
            self.trans_tree(tree2)
            return [self.post_processor(trans) for trans in Parser.gen_tree(tree2)]
        except ParseError as pe:
            return pe.args
        except UnifyError as ue:
            return ue.args
        
    
    def trans_file(self,infile,outfile):
        """ parses all sentences in infile. Each line should be in the form: InputSentence [ "@" ExpectedTranslation ]
        input and corresponding translations are written to output file. The file is appended by statistics (InputCount,TranslatedCount,MatchedCount)
        """
        input_cnt = 0
        trans_cnt = 0
        match_cnt = 0
        processor = DummyProcessor()
        with open(infile, 'r') as fin, open(outfile, 'w') as fout:
            for line in fin:
                line = line.strip()
                if not line:
                    continue
                input_cnt += 1
                line = line.split('@')
                if len(line) == 2:
                    if self.reverse:
                        trans,sent = line
                    else:
                        sent,trans = line
                else:
                    if sent.reverse:
                        raise ParseError("Input sentence doesn't contain translation", line)
                    sent = line[0]
                    trans = None
                
                trans = processor(trans)
                        
                print("input:"," @ ".join([sent,trans]),file=fout)
                print("output:",file=fout)
                trans_list = self.trans_sent(sent)
                print(sent, trans_list)
                if type(trans_list)==str: # an error occured
                    print(trans_list,file=fout)
                else:
                    trans_cnt += 1
                    if trans and trans in trans_list:
                        match_cnt += 1                    
                    for idx, alt in enumerate(trans_list):
                        print(idx+1,alt,file=fout)
                print(file=fout)
            print("input={}, translated={}, matched={}".format(input_cnt,trans_cnt,match_cnt),file=fout)
            

def main():
    logging.basicConfig(level=logging.DEBUG,filename="parser.log",filemode="w")
    
    parser = Parser()
    parser.pre_processor = EnglishPreProcessor()
    parser.post_processor = TurkishPostProcessor()

    try:
        #parser.load_grammar("_sample.grm")
        #sent = "i saw the man in the house with the telescope"
        parser.load_grammar("tenses.grm")
        #sents = ["i am watching you", "you are watching it", "men are watching her"]
        #sents = ["ben seni seyrediyorum", "sen onu seyrediyorsun", "adamlar onu seyrediyorlar"]
        sents = [ "i went" ]

        parser.compile()
        #print(parser.rules)
        for sent in sents:
            try:
                parser.parse(sent)
                #parser.print_parse_tables()
                tree = parser.make_tree()
                print(tree)
                print(Parser.pformat_tree(tree))
                tree2 = parser.unify_tree(tree)
                print(Parser.pformat_tree(tree2,2))
                parser.trans_tree(tree2)
                print(Parser.pformat_tree(tree2,3))
                """
                print(Parser.get_tree(tree))
                print(Parser.get_tree(ttree))       
                print(parser.xlate_tree(tree))
             

                morpher = Morpher()
                """
                print("==================================")
                print("input:", sent)
                print("output:")
                for no,alt in enumerate(Parser.gen_tree(tree2)):
                    print(no+1, alt, " ==> ", parser.post_processor(alt))
                    #print(no+1,alt)

            except ParseError as pe:
                print(pe.args)
            except UnifyError as ue:
                print(ue.args)
    except GrammarError as ge:
        print(ge.args)

def file_main():
    logging.basicConfig(level=logging.DEBUG,filename="parser.log",filemode="w")
    
    parser = Parser()
    parser.pre_processor = EnglishPreProcessor()
    parser.post_processor = TurkishPostProcessor()

    parser.load_grammar("tenses.grm")
    parser.compile()

    parser.trans_file("tenses.in.txt","tenses.out.txt")
    
if __name__ == "__main__":
    # execute only if run as a script
    main()
