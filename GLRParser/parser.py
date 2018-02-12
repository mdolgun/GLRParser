""" A GLR Parser for Natural Language Processing and Translation

(c) 2018 by Mehmet Dolgun, m.dolgun@yahoo.com

All functionality is provided by main class: Parser
The input grammar should be a list of rules in the form:
    NonTerminal "->" (SourceTerminal | NonTerminal)* [ ":" (DestTerminal|NonTerminal)* ] "#" Comment
empty lines and any characters after "#" are ignored
    
Sample grammar for English -> Turkish translation (see sample.grm)
S -> NP VP : NP VP
S -> S in NP : S NP -de
S -> S with NP : S NP -la
NP -> i : 
NP -> the man : adam
NP -> the telescope : teleskop
NP -> the house : ev
NP -> NP-1 in NP-2 : NP-2 -deki NP-1
NP -> NP-1 with NP-2 : NP-2 -lu NP-1
VP -> saw NP : NP -ı gördüm
   
"""
import logging
from collections import defaultdict

class ParseError(Exception):
    """ Raised when a sentence cannot be parsed with current grammar """
    pass

class GrammarError(Exception):
    """ Raised when a grammar cannot be parsed """
    pass

class Parser:
    """ A GLR Parser for Natural Language Processing and Translation

		see main() for sample usage

        internal data:
            rules : list of rules as tuples (head,body,trans) for a rule "head -> body : trans"
            ruledict : maps NT -> list of rulenos in "rules"
            nullable : set of nullable NTs, an NT is nullable if it can produce directly or indirectly an empty string
            dfa : Deterministic Finite Automaton for state transitions, where dfa[state,symbol] -> nextstate
            reduce : maps a state to a list of reductions  reduce[state] -> [(ruleno,rulepos)*]
            ereduce : maps a state to a list of empty reductions  ereduce[state] -> [(ruleno,rulepos)*]
    """     
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
            
    def get_rules(self):
        return "\n".join(
            ["{} -> {} : {}".format(
                head,
                " ".join(src),
                " ".join(map(str,dst))
            )
            for head,src,dst in self.rules
        ])
         
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
        
        for ruleno,(head,body,trans) in enumerate(rules):
            ruledict[head].append(ruleno)

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
   
    def split_grammar(self,iterator):
        """ get a list of grammar rules from iterator, splits and transforms it into list "rules"

        e.g. each rule S -> A B c : d B A becomes [S, [A, B, c], [d, 1, 0]],  where A,B is Non-Terminal c,d is Terminal
        todo: write a full parser with error detection
        """

        rules = [ ("S'", ["S"], [0]) ]
        for rule in iterator:
            rule = rule.split("#")
            rule = rule[0].strip()
            if not rule: # skip blank rules
                continue
            rule = rule.split("->")
            if len(rule)!=2:
                raise GrammarError("Invalid Grammar Rule", rule)
            body = rule[1].split(":")
            src = [] # e.g NP and NP
            src2 = [] # e.g NP-1 and NP-2
            for symbol in body[0].split(" "):
                if not symbol: continue
                sparts = symbol.split("-")
                src.append(sparts[0])
                src2.append(symbol)
            
            dst = []
            if len(body)==2: # there is a translation        
                for symbol in body[1].split(" "):
                    if not symbol: continue
                    try:                   
                        dst.append(src2.index(symbol))
                    except ValueError:
                        dst.append(symbol)
            rules.append([rule[0].strip(), src, dst])
            
        self.rules = rules
        if logging.getLogger().isEnabledFor(logging.INFO):
            logging.info("rules=%s",self.get_rules())

    def load_grammar(self,filename):
        """ loads a grammar file and parse it """
        with open(filename, "r") as f:
            self.split_grammar(f)

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

    def trans_prod(self,tree):
        # tree = [head, ruleno, symbol*]
        # return [head, ruleno, tsymbol*]
        if type(tree) == str: # if a terminal node, normally it shouldn't come here
            return tree
        trans = tree[0:2]
        for item in self.rules[tree[1]][2]:
            if type(item)==str:
                trans.append(item)
            else:
                trans.append(self.trans_tree(tree[item+2]))
        return trans
  
    def trans_tree(self,tree):
        # tree = [alt*] list of alternative for a production
        # returns [talt*] list of alternative translations for a production
        return [self.trans_prod(alt) for alt in tree]
         
    def pget_tree(tree,indent=""):
        # tree = [alt*] list of alternative for a production
        if type(tree) == str:
            return indent + tree
        def pget_prod(tree,indent):
            if type(tree) == str:
                return indent + tree
            if len(tree)==2:
                return indent + tree[0] + "[" + str(tree[1]) + "]()"
            else:
                return indent + tree[0] + "[" + str(tree[1]) + "](\n"+ "\n".join([pget_tree(sub,indent + "+---") for sub in tree[2:]]) + "\n" + indent + ")"
        return ("\n"+ indent + "|\n").join([pget_prod(alt,indent) for alt in tree])

    def get_edge_item(alts):
        return " ".join(["{2}({0},{1};{3},{4})".format(*alt) for alt in alts[1:]])
      
    def get_edge(self,edge):
        if edge not in self.edges:
            return "{2}({0},{1};{3},{4}) -> None".format(*edge)
        return  "{2}({0},{1};{3},{4}) -> ".format(*edge) + " | ".join( [ " ".join(["{2}({0},{1};{3},{4})".format(*alt) for alt in alts[1:]]) for alts in self.edges[edge]] )       
    
    def gen_prod(prod,skip=0):
        if len(prod)==skip:
            yield ""
            return
        for first in Parser.gen_tree(prod[skip]):
            for rest in Parser.gen_prod(prod[skip+1:]):
                if first and rest:
                    yield first + " " + rest
                else:
                    yield first or rest
          
    def gen_tree(tree):
        if type(tree) != list:
            yield tree
            return
        for prod in tree:
            yield from Parser.gen_prod(prod,2)  
  
    def print_parse_tables(self):
        indent = 7
        space = " "*indent
        for pos,token in enumerate(self.instr):
            print(str(pos).rjust(2,"-"),token.center(indent-2,"-"),sep="",end="")
        print()
        for (epos,estate,symbol),startset in sorted(self.nodes.items()):
            for spos,sstate in startset:
                print(space*spos, str(sstate).rjust(2), symbol.center((epos-spos)*indent-2,"="), str(estate).rjust(2,"="), " ", self.get_edge((spos,sstate,symbol,epos,estate)), sep="")
 
    def make_tree(self,edge=None):
        """ generates a tree (which is a recursive list of lists) from edges """

        if edge is None:
            edge = self.top_edge
        if edge not in self.edges:
            return edge[2]
        alts = self.edges[edge]
        talt = []
        for alt in alts:
            t = [edge[2],alt[0]]
            for alt_edge in alt[1:]:
                t.append(self.make_tree(alt_edge))
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
                logging.debug("Checking Work Item: %s ", edge)
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
                            edge = (ppos,pstate,head,pos,nstate) 
                            if edge not in edges:
                                rlist.append(edge)
                            ptree = [ruleno] + ptree
                            logging.debug("appending edge %s to %s", Parser.get_edge_item(ptree), self.get_edge(edge))
                            edges[edge].append(ptree)

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
                    logging.errror("Parse not possible")
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
    

def main():
    logging.basicConfig(level=logging.INFO,filename="parser.log")
    
    parser = Parser()

    try:
        parser.load_grammar("sample.grm")
        sent = "i saw the man in the house with the telescope"

        parser.compile()
        parser.parse(sent)
        #parser.print_parse_tables()
        tree = parser.make_tree()
        ttree = parser.trans_tree(tree)
        print(Parser.get_tree(tree))
        print(Parser.get_tree(ttree))       
        print(parser.xlate_tree(tree))

        for no,alt in enumerate(Parser.gen_tree(ttree)):
            print(no+1, alt.replace(" -",""))
            #print(no+1,alt)
    except ParseError as pe:
        print(pe.args)
    except GrammarError as ge:
        print(ge.args)

if __name__ == "__main__":
    # execute only if run as a script
    main()
