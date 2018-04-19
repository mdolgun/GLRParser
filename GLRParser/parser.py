""" A GLR Parser for Natural Language Processing and Translation

(c) 2018 by Mehmet Dolgun, m.dolgun@yahoo.com

This file define classes:
    Parser: main functionality for parsing, feature unification and translation
    ParserError,UnifyError: exceptions thrown when parsing or unification fails
      
"""
import logging, re, copy
from collections import defaultdict

if __name__ == "__main__":
    from morpher import TurkishPostProcessor
    from grammar import Grammar,GrammarError,Rule,format_feat,Trie
    from tree import Tree,uid
else:
    from .morpher import TurkishPostProcessor
    from .grammar import Grammar,GrammarError,Rule,format_feat,Trie
    from .tree import Tree,uid

empty_dict = dict()
empty_set = set()
empty_list = list()

class ParseError(Exception):
    """ Raised when a sentence cannot be parsed with current grammar """
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

class DummyPreProcessor:
    """ Dummy pre processor used in Parser """
    def __call__(self,sent):
        return sent.strip()

class DummyPostProcessor:
    """ Dummy post processor used in Parser """      
    def __call__(self,sent):
        return sent

class DefPreProcessor:
    """ Default pre processor used in Parser """
    def __init__(self):
        self.regex = re.compile("[ ,.?:;()]+")
        
    def __call__(self,sent):
        return self.regex.sub(' ',sent).strip()  

class DefPostProcessor:
    """ Default post processor used in Parser """
        
    def __call__(self,sent):
        return sent.replace(" -","")

class Parser:
    """ A GLR Parser for Natural Language Processing and Translation

		see main() for sample usage

        internal data:
            rules : list of rules as named tuple Rule(head,left,right,feat,lparam,rparam,lcost,rcost) 
            ruledict : maps NT -> list of rulenos in "rules"
            nullable : set of nullable NTs, an NT is nullable if it can produce directly or indirectly an empty string
            dfa : Deterministic Finite Automaton for state transitions, where dfa[state,symbol] -> nextstate
            reduce : maps a state to a list of reductions  reduce[state] -> [(ruleno,rulepos)*]
            ereduce : maps a state to a list of empty reductions  ereduce[state] -> [(ruleno,rulepos)*]
    """
    pre_processors  = { None: DummyPreProcessor, "": DefPreProcessor,  "EN": EnglishPreProcessor,  "TR": TurkishPreProcessor }
    post_processors = { None: DummyPreProcessor, "": DefPostProcessor, "EN": EnglishPostProcessor, "TR": TurkishPostProcessor }

    def __init__(self,pre_process="",post_process="",reverse=False):
        """ initializes parser with pre_processor and post_processor, which should be callable, reverse reverses(i.e. swaps) the input/output grammars """
        self.pre_processor  = self.pre_processors[pre_process]()
        self.post_processor = self.post_processors[post_process]()
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
                while symbol in self.nullable:
                    rulepos += 1
                    nextstate = (ruleno,rulepos)
                    if nextstate not in stateset: 
                        stateset.add(nextstate)
                        todo.append(nextstate)              
                    symbol = self.rules[ruleno][1][rulepos]
                """
            except IndexError: # there is no more symbols in the rule (i.e. A->x.)
                pass

    def format_rules(self):
         return "\n".join([rule.format() for rule in self.rules])
         
    def get_items(self,stateset):
        """ get string repr of "items" in state set in dotted fomat  e.g "{ S -> NP . VP ; VP -> . V  ; VP -> . V NP }" """
        slist = ["{"]
        for ruleno,rulepos in stateset:
            slist.append("{} -> {} . {}".format(self.rules[ruleno][0], " ".join(self.rules[ruleno][1][0:rulepos]), " ".join(self.rules[ruleno][1][rulepos:])))
        slist.append("}")
        return " , ".join(slist)

    def get_item(self,ruleno,rulepos):
        return "{} -> {} . {}".format(self.rules[ruleno][0], " ".join(self.rules[ruleno][1][0:rulepos]), " ".join(self.rules[ruleno][1][rulepos:]))    

    def compile(self):
        """ compile rule list "rules" to a DFA

        produces dfa, reduce and ereduce tables(dictionaries) from rules
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
   
    def load_grammar(self,fname=None,reverse=False,text=None):
        """ loads a grammar file and parse it """
        self.rules,self.trie = Grammar.load_grammar(fname,reverse,text)

        if logging.getLogger().isEnabledFor(logging.INFO):
            logging.info("rules=%s",self.format_rules())

    def unify_up(dst,param,src):
        """ unification of "src" features into "dst" features, using filtering of "param", if unification fails raises UnifyError

        if param is None, src is directly unified into dst
        otherwise param contains a pre-condition dict and a filter set,
        src is checked against pre-condition dict and then filtered with filter set and unified into dst

        """
        if param is None:
            keys = src.keys()
        else:
            keys = set()
            for key in param.keys() & src.keys():
                if param[key] is None:
                    keys.add(key)
                else:
                    val = param[key]
                    if val[0] == '*':
                        val = dst.get(val[1:])
                    if val:
                        if val != src[key]:
                            raise UnifyError("Unify precheck error feat=%s src=%s param=%s" % (key, src[key], val))

        newkeys = keys - dst.keys()
        for key in keys & dst.keys():
            if  src[key] != dst[key]:
                if dst[key] == '-':
                    newkeys.add(key)
                elif src[key] == '-':
                    pass
                elif dst[key] == '+':
                    newkeys.add(key)
                elif src[key] == '+':
                    pass
                else:
                    raise UnifyError("Unify error feat=%s src=%s param=%s" % (key, src[key], dst[key]))

    
        if newkeys:
            dst = dst.copy()
            for key in newkeys:
                dst[key] = src[key]
        return dst

    def unify_down(dst,param,src):
        """ unification of "src" features into "dst" features, using filtering of "param", if unification fails raises UnifyError

        if param is None, src is directly unified into dst
        otherwise param contains a pre-condition dict and a filter set,
        dst is unified against pre-condition dict and filtered src

        """
        if param is None:
            pdict = src
        else:
            pdict = dict()
            for key in param.keys():
                if param[key] is None:
                    if key in src:
                        pdict[key] = src[key]
                else:
                    val = param[key]
                    if val[0] == '*':
                        val = src.get(val[1:])
                    if val:
                        pdict[key] = val

        newkeys = pdict.keys() - dst.keys()
        for key in pdict.keys() & dst.keys():
            if pdict[key] != dst[key]:
                if pdict[key] == '+' and dst[key] != '-':
                        pass
                elif dst[key] == '+' and pdict[key] != '-':
                    newkeys.add(key)
                else:
                    raise UnifyError("UnifyD error feat=%s src=%s param=%s" % (key, pdict[key], dst[key]))
        if newkeys:
            dst = dst.copy()
            dst.update(pdict)
        return dst

 
    def unify_tree(self,tree):
        """ bottom-up unifies a tree and returns a new tree """
        rule = self.rules[tree.ruleno]
        fdict,srcflist = rule.feat, rule.lparam
        stack = [(fdict,[])]
        for item,param in zip(tree.left,srcflist):
            if type(item)==str:
                for fdict,seq in stack:
                    seq.append(item)
            else:
                nstack = []
                for fdict,seq in stack:
                    nkeys = []
                    nvals = []
                    for alt in item:
                        try:
                            subtrees = self.unify_tree(alt)
                        except UnifyError as ue:
                            last_error = ue.args[0]
                            continue
                        for subtree in subtrees:
                            logging.debug("Unify feat=%s param=%s subfeat=%s ", format_feat(fdict), format_feat(param), format_feat(subtree.feat))
                            try:      
                                _fdict = Parser.unify_up(fdict,param,subtree.feat)
                                logging.debug("Unify Success=%s", format_feat(_fdict))
                                try:
                                    idx = nkeys.index(_fdict)
                                    nvals[idx].append(subtree) 
                                except ValueError:
                                    nkeys.append(_fdict)
                                    nvals.append([subtree])
                                #print("nkeys=%s nvals=%s" % (nkeys,nvals))
                            except UnifyError as ue:
                                logging.debug("Unify Failure dst=%s param=%s src=%s ", format_feat(fdict), format_feat(param), format_feat(subtree.feat))
                                last_error = "%s super=%s#%d sub=%s#%d" % (ue.args[0], tree.head, tree.ruleno, subtree.head, subtree.ruleno)
                    for key,val in zip(nkeys,nvals):
                        nstack.append((key,seq+[val]))
                stack = nstack
                if not stack: # if unification of all alternative sub-trees fails, re-raises the last error
                    logging.debug("Re-raising UnifyError %s" % last_error)
                    raise UnifyError(last_error)
        ntree = []
        for fdict,seq in stack:
            ntree.append(Tree(tree.head,tree.ruleno,seq,tree.right,fdict,tree.cost))
        if tree.head=="S'":
            assert len(ntree)==1
            return ntree[0]
        return ntree

    def prune(alts):
        cost = min(subtree.cost for subtree in alts)
        if cost<0:
            alts = [subtree for subtree in alts if subtree.cost==cost]
            for subtree in alts:
                subtree.cost = 0
        return alts

    def make_trans_tree(self,symbol,feat,fparam):
        """ generate a tree for dst-only non-terminal tree """
        ntree = []
        for ruleno in self.ruledict[symbol]:
            rule = self.rules[ruleno]
            try:
                #logging.debug("make_trans_tree1: %s unifyd(%s,%s,%s)", symbol, format_feat(feat), format_feat(fparam,'()'), format_feat(rule.feat))
                fdict = Parser.unify_down(rule.feat,fparam,feat)
                logging.debug("make_trans_tree: %s unifyd(%s,%s,%s)->%s", symbol, format_feat(feat), format_feat(fparam,'()'), format_feat(rule.feat), format_feat(fdict))
                sub = []
                for item,param in zip(rule.right,rule.rparam):
                    assert type(item) != int, "%s#%d(%s) %s:%s" % (symbol,ruleno,fparam,item,param)
                    if param is False: # Terminal
                        sub.append(item)
                    else: # NonTerminal
                        sub.append(Parser.prune( self.make_trans_tree(item,fdict,param) ))
                ntree.append(Tree(symbol,ruleno,[],sub,fdict,rule.cost)) 
            except UnifyError as ue:
                last_error = "%s %s#%d" % (ue.args[0], symbol, ruleno)
                logging.debug("make_trans_tree: %s unifyd(%s,%s,%s)->Error", symbol, format_feat(feat), format_feat(fparam,'()'), format_feat(rule.feat))
        if not ntree:
            raise UnifyError(last_error)
        return ntree

    def trans_tree(self,tree,feat=empty_dict,fparam=None):
        """ translates and unifies translation(right) part of a parse tree
        returns a modified version of the node "tree" """

        assert type(tree)==Tree
        tree = copy.copy(tree) # MD 12.04.2018
        logging.debug("trans_tree: %s unify(%s,%s,%s)->", tree.head, format_feat(tree.feat), format_feat(fparam,'()'), format_feat(feat))                       
        fdict = Parser.unify_down(tree.feat,fparam,feat)
        logging.debug("trans_tree: ->%s", format_feat(fdict))                       
        rule = self.rules[tree.ruleno]
        trans = []
        for item,param in zip(rule.right,rule.rparam):
            if param is False: # Terminal
                trans.append(item)
            elif type(item)==str: # Unmatched (Right-Only) NT
                assert item[0].isupper()
                trans.append(Parser.prune( self.make_trans_tree(item,fdict,param) )) 
            else: # Matched (Left&Right) NT
                assert type(item)==int
                trans.append(Parser.prune( [self.trans_tree(alt,fdict,param) for alt in tree.left[item]] ))           
        tree.right = trans
        return tree

    def format_edge_item(alts):
        """ internal: format an edge item to str (used internally for logging/debugging) """
        return " ".join(["{2}({0},{1};{3},{4})".format(*alt) if type(alt)==tuple else " ".join(alt)
                         for alt in alts[1:]])
      
    def format_edge(self,edge):
        """ internal: format an edge into str (used internally for logging/debugging) """
        if edge not in self.edges:
            if type(edge)==tuple:
                return "{2}({0},{1};{3},{4}) -> None".format(*edge)
            else:
                return " ".join(edge)
        return  "{2}({0},{1};{3},{4}) -> ".format(*edge) + " | ".join( [ " ".join(
            ["{2}({0},{1};{3},{4})".format(*alt) if type(alt)==tuple else alt
             for alt in alts[1:]]) for alts in self.edges[edge]] )       
    
    def print_parse_tables(self):
        """ internal: print parse tables after parse """
        indent = 7
        space = " "*indent
        for pos,token in enumerate(self.instr):
            print(str(pos).rjust(2,"-"),token.center(indent-2,"-"),sep="",end="")
        print()
        for (epos,estate,symbol),startset in sorted(self.nodes.items()):
            for spos,sstate in startset:
                print(space*spos, str(sstate).rjust(2), symbol.center((epos-spos)*indent-2,"="), str(estate).rjust(2,"="), " ", self.format_edge((spos,sstate,symbol,epos,estate)), sep="")

    def make_tree(self):
        self.tree = Tree(
            head = "S'",
            ruleno = 0,
            left = [self.make_tree_int(self.top_edge)]
        )
        return self.tree

    def make_tree_int(self,edge):
        """ generates a tree (which is a recursive list of lists) from edges """
        if edge not in self.edges:
            if type(edge)==tuple: #(state1,pos1,term,state2,pos2)
                return edge[2]
            else: # list of non-terminals
                return edge;
        alt = []
        for alt_edge in self.edges[edge]: 
            ruleno = alt_edge[0]
            if type(ruleno)==int:
                rule = self.rules[ruleno]
            else:
                rule = ruleno
                ruleno = None

            alt.append( Tree(
                head = edge[2],
                ruleno = ruleno, ### Check!!!
                left = [self.make_tree_int(sub_edge) for sub_edge in alt_edge[1:]],
                right = rule.right,#.copy(),
                feat = rule.feat,
                cost = rule.cost
            ) )
        return alt

    def print_dfa(self):
        """ internal: prints dfa, reduce and e-reduce in a tabular format after compile """
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

        act_states = [set() for i in range(inlen)] # active set of states for each position
        act_edges  = [set() for i in range(inlen)] # active set of edges for each position

        act_states[0].add(0); # add initial state to initial position

        
        for pos in range(inlen):
            token = instr[pos]         
             
            rlist = list(act_edges[pos])
            active = act_states[pos]

            logging.debug("act_states=%s act_edges=%s", active, rlist)

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

            actlist = list(active)

            for state in actlist:
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
                        if nstate not in active:
                            active.add(nstate)
                            actlist.append(nstate)
                        nodes[pos,nstate,head].add((pos,state))
                        nedge = (pos,state,head,pos,nstate)
                        logging.debug("appending edge %s to %s", Parser.format_edge_item(ptree), self.format_edge(nedge))
                        edges[nedge].append(ptree)
      
            logging.debug("active=%s input= %s", active, token)
            if token == "$":
                if fstate in active:
                    logging.info("Parse successful")
                else:
                    while not act_states[pos]:
                        pos -= 1
                    logging.error("Parse not possible: %s >> %s"," ".join(instr[0:pos])," ".join(instr[pos:]))
                    raise ParseError("Parse not possible: %s >> %s" % (" ".join(instr[0:pos])," ".join(instr[pos:])))
            else:
                if not active:
                    continue
                    #logging.error("not active, %s",active)
                    #raise ParseError("Cannot shift %s<< %s" % (" ".join(instr[0:pos])," ".join(instr[pos:])))

                for state in active:
                    nstate = dfa.get((state,token),-1)
                    #print(state,",",token,"->",nstate)
                    if nstate != -1:                       
                        logging.debug("add nodes[%s] = %s",(pos+1,nstate,token),(pos,state)) 
                        nodes[pos+1,nstate,token].add((pos,state))
                        logging.debug("shift %s = %s", (pos+1,nstate,token,pos,state),token)
                    
                        act_edges[pos+1].add((pos,state,token,pos+1,nstate))
                        act_states[pos+1].add(nstate)

                items = self.trie.search(instr[pos:])
                logging.debug("Shift pos: %d items: %s", pos, items)
                #items.append((1,(token,[],[]))
                for input_len,rule in items:
                    token = rule.head
                    nextpos = pos + input_len
                    for state in active:
                        nstate = dfa.get((state,token),-1)
                        if nstate != -1:                           
                            logging.debug("add nodes[%s] = %s",(nextpos,nstate,token),(pos,state)) 
                            nodes[nextpos,nstate,token].add((pos,state))
                            nedge = (pos,state,token,nextpos,nstate)
                            logging.debug("shift %s = %s", nedge, token)
                    
                            act_edges[nextpos].add(nedge)
                            act_states[nextpos].add(nstate)

                            edges[nedge].append([rule]+rule.left)
                            #logging.debug("appending edge %s to %s", Parser.format_edge_item(ptree), self.format_edge(nedge))

    def trans_sent(self,sent):
        """ translates a sentence, returns a list of possible translations or an error """
        try:
            sent = self.pre_processor(sent)
            self.parse(sent)
            tree = self.make_tree()
            tree2 = self.unify_tree(tree)
            tree3 = self.trans_tree(tree2)
            return [(self.post_processor(trans),cost) for trans,cost in tree3.enumx()]
            #return list(tree3.enumx())
        except ParseError as pe:
            return str(pe)
        except UnifyError as ue:
            return str(ue)
        
    
    def trans_file(self,infile,outfile,ignore_exp_error=False):
        """ parses all sentences in infile. Each line should be in the form: InputSentence [ "@" ExpectedTranslation ]
        input and corresponding translations are written to output file. The file is appended by statistics (InputCount,TranslatedCount,MatchedCount)
        """
        input_cnt = 0
        trans_cnt = 0
        match_cnt = 0
        experr_cnt = 0
        ignore_cnt = 0
        pre_processor = DummyPreProcessor()
        with open(infile, 'r') as fin, open(outfile, 'w') as fout:
            for line in fin:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                input_cnt += 1
                parts = line.split('@')
                if len(parts) == 2: # input file contains the expected translation
                    if self.reverse:
                        trans,sent = parts
                    else:
                        sent,trans = parts
                    trans = [pre_processor(tsent) for tsent in trans.split('|')]
                else:
                    if self.reverse:
                        raise ParseError("Input sentence doesn't contain translation", line)
                    sent = parts[0]
                    trans = []

                sent = sent.strip()
                if sent == '*': # reverse translation for expected parse error
                    continue
                        
                print("input:"," @ ".join([sent.strip()," | ".join(trans)]),file=fout)
                print("output:",file=fout,end=" ")
                trans_list = self.trans_sent(sent)
                #print(sent, trans_list)
                if type(trans_list)==str: # an error occured
                    if '*' in trans:
                        experr_cnt += 1
                        print("EXPECTED ERROR",file=fout)
                    else:
                        print("ERROR",file=fout)
                    print(trans_list,file=fout)
                else:
                    trans_list, trans_cost = zip(*trans_list)
                    trans_cnt += 1
                    if trans==[] or trans==['*'] and ignore_exp_error:
                        print("IGNORED",file=fout)
                        ignore_cnt += 1
                    elif any(tsent in trans_list for tsent in trans):
                        print("OK",file=fout)
                        match_cnt += 1  
                    else:
                        print("NOK",file=fout)
                    for idx, alt in enumerate(trans_list):
                        print(idx+1,alt,trans_cost[idx],file=fout)
                print(file=fout)
            print("input={}, translated={}, matched={} exp_err={} ignored={}".format(input_cnt,trans_cnt,match_cnt,experr_cnt,ignore_cnt),file=fout)
        return (input_cnt,trans_cnt,match_cnt,experr_cnt,ignore_cnt)
            

