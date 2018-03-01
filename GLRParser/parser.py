""" A GLR Parser for Natural Language Processing and Translation

(c) 2018 by Mehmet Dolgun, m.dolgun@yahoo.com

All functionality is provided by main class: Parser
The input grammar should be a list of rules in the form:
    NonTerminal "->" (SourceTerminal | NonTerminal)* [ ":" (DestTerminal|NonTerminal)* ] "#" Comment
empty lines and any characters after "#" are ignored
      
"""
import logging, re
from collections import defaultdict,namedtuple

if __name__ == "__main__":
    from morpher import TurkishPostProcessor
    from grammar import Grammar,GrammarError,Rule,format_feat
else:
    from .morpher import TurkishPostProcessor
    from .grammar import Grammar,GrammarError,Rule,format_feat

Tree = namedtuple('Tree', 'head, ruleno, left, right, feat')

def format_tree(self,tree_type=2):
    """ returnes single-line formatted string representation of a tree """
    return " ".join([
        item if type(item)==str
        else "{}({})".format(item[0].head,"|".join([format_tree(alt,tree_type) for alt in item]))
        for item in self[tree_type]
        ])

def str_tree(self,tree_type=2):
    """ return string representation of terminals where alternative strings are in the form: (alt1|alt2|...) """
    return " ".join([
        item if type(item)==str 
        else str_tree(item[0]) if len(item)==1
        else "("+"|".join([str_tree(alt,tree_type) for alt in item])+")"
        for item in self[tree_type]
        ])

indenter = "    "
def pformat_tree(self,tree_type=2,level=0):
    """ return prety formatted (indented multiline) string representation of a tree """
    indent = indenter*level
    return "".join([
        "{}{}\n".format(indent,item) if type(item)==str
        else "{indent}{head}({body})\n".format(
            indent=indent,
            head=item[0].head,
            body=" ".join(item[0][tree_type])    
        ) if len(item)==1 and all(map(lambda x:type(x)==str,item[0][tree_type]))
        else "{indent}{head}(\n{body}{indent})\n".format(
            indent=indent,
            head=item[0].head,
            body=(indent+"|\n").join([pformat_tree(alt,tree_type,level+1) for alt in item])  
        )
        for item in self[tree_type]
    ])

def pformat_tree_ext(self,tree_type=2,level=0):
    """ return prety formatted (indented multiline) string representation of a tree with extended information(rule no, feature list) """
    indent = indenter*level
    if len(self[tree_type])==0: # empty production
        return ""
    if all(map(lambda x:type(x)==str,self[tree_type])): # terminal-only production
        return  indent+" ".join(self[tree_type])+"\n"
    return "".join([
        "{}{}\n".format(indent,item) if type(item)==str
        else "{indent}{head}(\n{body}{indent})\n".format(
            indent=indent,
            head=item[0].head,
            body=(indent+"|\n").join([
                "{indent}#{ruleno}{feat}\n{body}".format(
                    indent=indent,
                    ruleno=alt.ruleno,
                    feat=format_feat(alt.feat),
                    body = pformat_tree_ext(alt,tree_type,level+1)
                )
                for alt in item
            ])    
        )
        for item in self[tree_type]
    ])

Tree.format = format_tree
Tree.pformat = pformat_tree
Tree.pformat_ext = pformat_tree_ext
Tree.str_format = str_tree

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

    def format_rules(self):
         return "\n".join([rule.format() for rule in self.rules])
         
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
        self.rules = Grammar.load_grammar(fname,reverse,text)
        if logging.getLogger().isEnabledFor(logging.INFO):
            logging.info("rules=%s",self.format_rules())

    def unify(dst,param,src):
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
                elif param[key] != src[key]:
                    raise UnifyError("Unify error feat=%s src=%s param=%s" % (key, src[key], param[key]))

        for key in keys & dst.keys():
            if  src[key] != dst[key]:
                raise UnifyError("Unify error feat=%s src=%s param=%s" % (key, src[key], dst[key]))

        newkeys = keys - dst.keys()
        if newkeys:
            dst = dst.copy()
            for key in newkeys:
                dst[key] = src[key]
        return dst
 
    def unify_tree(self,tree):
        # tree.left=[(str|subtree+)*]
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
                        for subtree in self.unify_tree(alt):               
                            try:
                                _fdict = Parser.unify(fdict,param,subtree.feat)
                                try:
                                    idx = nkeys.index(_fdict)
                                    nvals[idx].append(subtree) 
                                except ValueError:
                                    nkeys.append(_fdict)
                                    nvals.append([subtree])
                            except UnifyError as ue:
                                last_error = "%s super=%s#%d sub=%s#%d" % (ue.args[0], tree.head, tree.ruleno, subtree.head, subtree.ruleno)
                    for key,val in zip(nkeys,nvals):
                        nstack.append((key,seq+[val]))
                stack = nstack
                if not stack:
                    raise UnifyError(last_error)
        ntree = []
        for fdict,seq in stack:
            ntree.append(Tree(tree.head,tree.ruleno,seq,tree.right,fdict))
        if tree.head=="S'":
            assert len(ntree)==1
            return ntree[0]
        return ntree

    def make_trans_tree(self,symbol,feat,fparam):
        """ generate a tree for dst-only non-terminal tree """
        ntree = []
        for ruleno in self.ruledict[symbol]:
            rule = self.rules[ruleno] # (head,src,dst,feat,lparam,rparam,lcost,rcost)
            try:
                fdict = Parser.unify(feat,fparam,rule.feat)
                logging.debug("make_trans_tree: %s unify(%s,%s,%s)->%s", symbol, format_feat(feat), format_feat(fparam,'()'), format_feat(rule.feat), format_feat(fdict))
                sub = []
                for item,param in zip(rule.right,rule.rparam):
                    assert type(item) != int
                    if param is False: # Terminal
                        sub.append(item)
                    else: # NonTerminal
                        sub.append( self.make_trans_tree(item,fdict,param) )      
                ntree.append(Tree(symbol,ruleno,[],sub,fdict)) # [head, ruleno, [symbol*], [tsymbol*], featdict]
            except UnifyError:
                pass
        if not ntree:
            raise UnifyError("empty make_trans_tree")
        return ntree

    def trans_tree(self,tree,feat=empty_dict,fparam=None):
        # in  = [head, ruleno, [symbol*], None, featdict]
        # out = [head, ruleno, [symbol*], [tsymbol*], featdict]
        assert type(tree)==Tree
        fdict = Parser.unify(tree.feat,fparam,feat)
        logging.debug("trans_prod: %s unify(%s,%s,%s)->%s", tree.head, format_feat(tree.feat), format_feat(fparam,'()'), format_feat(feat), format_feat(fdict))                       
        rule = self.rules[tree.ruleno]
        trans = []
        for item,param in zip(rule.right,rule.rparam):
            if param is False: # Terminal
                trans.append(item)
            elif type(item)==str: # Unmatched (Right-Only) NT
                assert item[0].isupper()
                trans.append( self.make_trans_tree(item,fdict,param) ) 
            else: # Matched (Left&Right) NT
                assert type(item)==int
                trans.append([self.trans_tree(alt,fdict,param) for alt in tree.left[item]])
        return tree._replace(right=trans)

    def format_edge_item(alts):
        """ internal: format an edge item to str (used internally for logging/debugging) """
        return " ".join(["{2}({0},{1};{3},{4})".format(*alt) for alt in alts[1:]])
      
    def format_edge(self,edge):
        """ internal: format an edge into str (used internally for logging/debugging) """
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
            left = [self.make_tree_int(self.top_edge)],
            right = empty_list,
            feat = empty_dict
        )
        return self.tree

    def make_tree_int(self,edge):
        """ generates a tree (which is a recursive list of lists) from edges """
        if edge not in self.edges:
            return edge[2]
        alt = []
        for alt_edge in self.edges[edge]: 
            rule = self.rules[alt_edge[0]] 
            alt.append( Tree(
                head = edge[2],
                ruleno = alt_edge[0],
                left = [self.make_tree_int(sub_edge) for sub_edge in alt_edge[1:]],
                right = rule.right,
                feat = rule.feat
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
        """ translates a sentence, returns a list of possible translations or an error """
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
                print(tree.pformat())
                tree2 = parser.unify_tree(tree)
                print(tree2.pformat_ext())
                tree3 = parser.trans_tree(tree2)
                print(tree3.pformat(tree_type=3))
                print(tree3.str_format(tree_type=2))
                print(tree3.str_format(tree_type=3))
                print("==================================")
                print("input:", sent)
                print("output:")
                for no,alt in enumerate(Parser.gen_prod(tree3.right)):
                    #print(no+1, alt, " ==> ", parser.post_processor(alt))
                    print(no+1,alt)
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
    #print(parser.format_rules())
    parser.compile()

    parser.trans_file("tenses.in.txt","tenses.out.txt")
    
if __name__ == "__main__":
    # execute only if run as a script
    main()
