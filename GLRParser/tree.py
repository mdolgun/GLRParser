""" A GLR Parser for Natural Language Processing and Translation

(c) 2018 by Mehmet Dolgun, m.dolgun@yahoo.com

This file define classes:
    Tree: node of a parse tree
      
"""
if len(__name__.split("."))>1: # called within a package
    from .grammar import format_feat
else: # called as a module or script
    from grammar import format_feat

new_unify = False

empty_dict = dict()
empty_list = list()

uid_dict = dict()
uid_cnt = 0
def uid(obj):
    """ create globally unique id for an object, starting from 1) """
    global uid_cnt, uid_dict
    _id = id(obj)
    if _id in uid_dict:
        return uid_dict[_id]
    uid_cnt += 1
    uid_dict[_id] = uid_cnt
    return uid_cnt

from io import StringIO
def str_items_cost(items):
    out = StringIO()
    print_items_cost(items, out)
    return out.getvalue()

def print_items_cost(items,out):
    first_item = True
    for item in items:
        if first_item:
            first_item = False
        else:
            print(" ", end="", file=out)
        if isinstance(item, str):
            print(item, end="", file=out)
        else:
            print("(", end="", file=out)
            first = True
            for alt,cost in item:
                if first:
                    first = False
                else:
                    print("|", end="", file=out)
                if cost:
                    print("{", cost, "}", sep="", end="", file=out)
                print_items_cost(alt, out)
            print(")", end="", file=out)

def is_suffix(node):
    if isinstance(node, str):
        if node[0] in "+-":
            return True
    else:
        for alt,cost in node:
            if alt and is_suffix(alt[0]):
                return True
    return False

def combine_suffixes_lst(nodes,cost,out,new_options):
    for node in nodes:
        combine_suffixes(node, out)
    if len(out)==1 and not isinstance(out[0], str):
        for sub_nodes,sub_cost in out[0]:
            new_options.append((sub_nodes,cost+sub_cost))
    else:
        new_options.append((out,cost))

def combine_suffixes(node,out):
    prev_node = out[-1] if out else None
    if isinstance(node, str): # if current node is a terminal
        if prev_node and is_suffix(node):
            if isinstance(prev_node, str):
                out[-1] += " " + node
            else:
                for prev_nodes,cost in prev_node:
                    combine_suffixes(node, prev_nodes)
        else:
            out.append(node)
    elif prev_node and is_suffix(node): # there is a previous word, there multiple options, of which at least one starts with a suffix
        if isinstance(prev_node, str): # previous item is a terminal
            new_options = []
            for sub_nodes,cost in node:
                new_nodes = [prev_node]
                combine_suffixes_lst(sub_nodes,cost,new_nodes,new_options)
            out[-1] = new_options
        else: # previous item is a list of alternatives
            new_options = []
            for sub_nodes,cost in node:
                for prev_sub_nodes,prev_sub_cost in prev_node:
                    new_nodes = prev_sub_nodes.copy();
                    combine_suffixes_lst(sub_nodes,cost+prev_sub_cost,new_nodes,new_options)
            out[-1] = new_options
    else: # current node is an option list with no suffixes or prev_node is None
        new_options = []
        for sub_nodes,cost in node:
            new_nodes = []
            combine_suffixes_lst(sub_nodes,cost,new_nodes,new_options)
        out.append(new_options)

def post_process(option_list, post_processor):
    for idx,item in enumerate(option_list):
        if isinstance(item, str):
            option_list[idx] = post_processor(item)
        else:
            for alt,_cost in item:
                post_process(alt, post_processor)
class Tree:
    if not new_unify:
        __slots__ = ('head', 'rule', 'ruleno', 'left', 'right', 'feat', 'cost') 
        def __init__(self, head, rule, ruleno=None, left=empty_list, right=empty_list, feat=empty_dict, cost=0):
            self.head = head
            self.rule = rule
            self.ruleno = ruleno
            self.left = left
            self.right = right
            self.feat = feat
            self.cost = cost
    else:
        __slots__ = ('head', 'rule', 'ruleno', 'left', 'right') # (head, rule, ruleno, left, [(right, feat, cost)])
        def __init__(self, head, rule, ruleno=None, left=empty_list, right=empty_list, feat=empty_dict, cost=0):
            self.head = head
            self.rule = rule
            self.ruleno = ruleno
            self.left = left
            self.right = [(right,feat,cost)]


    def format(self):
        """ returnes single-line formatted string representation of a tree """
        return " ".join(
            item if isinstance(item, str)
            else "{}({})".format(item[0].head, "|".join(alt.format() for alt in item))
            for item in self.left
        )
    if not new_unify:
        def formatr(self):
            """ returnes single-line formatted string representation of a tree """
            return " ".join(
                item if isinstance(item, str)
                else "{}({})".format(item[0].head, "|".join(alt.formatr() for alt in item))
                for item in self.right
            )
    else:
        def formatr(self):
            return " ".join(
                item if isinstance(item, str)
                else "{}({})".format(item[0].head, "|".join(
                    alt.formatr() for alt in item
                ))
                for alt_right in self.right for item in alt_right[0]
            )

    def str_format(self):
        """ return string representation of terminals where alternative strings are in the form: (alt1|alt2|...) """
        return " ".join(
            item if isinstance(item, str)
            else item[0].str_format() if len(item)==1
            else "("+"|".join(alt.str_format() for alt in item)+")"
            for item in self.left
        )
    def str_formatr(self):
        """ return string representation of terminals where alternative strings are in the form: (alt1|alt2|...) """
        return " ".join(
            item if isinstance(item, str)
            else item[0].str_formatr() if len(item)==1
            else "("+"|".join(alt.str_formatr() for alt in item)+")"
            for item in self.right
        )
    """
    def convert(self):   
        return " ".join([
            item if type(item)==str 
            else "("+"|".join([convert_tree(alt) for alt in item])+")"
            for item in self
        ])
    """

    def list_format(self):
        """ return a list formatted left tree """
        out = []
        for item in self.left:
            if isinstance(item, str):
                out.append(item)
            elif len(item)==1:
                out.extend(item[0].list_format())
            else:
                out.append([alt.list_format() for alt in item])
        return out

    def list_formatr(self):
        """ return a list formatted right tree """
        out = []
        for item in self.right:
            if isinstance(item, str):
                out.append(item)
            elif len(item)==1:
                out.extend(item[0].list_formatr())
            else:
                out.append([alt.list_formatr() for alt in item])
        return out

    #def option_list(self):
    #    out = []
    #    for item in self.right:
    #        if type(item)==str:
    #            out.append(item)
    #        elif len(item)==1:
    #            out.extend(item[0].option_list())
    #        else:
    #            out.append([(alt.option_list(),alt.cost) for alt in item])
    #    return out

    def option_list(self):
        out = []
        cost = self.cost
        for item in self.right:
            if isinstance(item, str):
                out.append(item)
            elif len(item)==1:
                option,option_cost = item[0].option_list()
                cost += option_cost
                out.extend(option)
            else:
                options = []
                for alt in item:
                    option,option_cost = alt.option_list()
                    if len(option)==1 and not isinstance(option[0], str):
                        options.extend(option[0])
                    else:
                        options.append((option,option_cost))
                out.append(options)
        return out,cost

    indenter = "    "
    def pformat(self,level=0):
        """ return prety formatted (indented multiline) string representation of a tree """
        indent = self.indenter*level
        return "".join(
            "{}{}\n".format(indent,item) if isinstance(item, str)
            else "{indent}{head}({body})\n".format(
                indent=indent,
                head=item[0].head,
                body=" ".join(item[0].left)    
            ) if len(item)==1 and all(map(lambda x:isinstance(x,str),item[0].left))
            else "{indent}{head}(\n{body}{indent})\n".format(
                indent=indent,
                head=item[0].head,
                body=(indent+"|\n").join(alt.pformat(level+1) for alt in item)  
            )
            for item in self.left
        )
    def pformatr(self,level=0):
        """ return prety formatted (indented multiline) string representation of a tree """
        indent = self.indenter*level
        return "".join(
            "{}{}\n".format(indent,item) if isinstance(item, str)
            else "{indent}{head}({body})\n".format(
                indent=indent,
                head=item[0].head,
                body=" ".join(item[0].right)    
            ) if len(item)==1 and all(map(lambda x:isinstance(x,str),item[0].right))
            else "{indent}{head}(\n{body}{indent})\n".format(
                indent=indent,
                head=item[0].head,
                body=(indent+"|\n").join(alt.pformatr(level+1) for alt in item)  
            )
            for item in self.right
        )

    def pformat_ext(self,level=0):
        """ return prety formatted (indented multiline) string representation of left tree with extended information(rule no, feature list, cost) """
        indent = self.indenter*level
        prod = self.left
        if len(prod)==0: # empty production
            return ""
        if all(map(lambda x:isinstance(x,str),prod)): # terminal-only production
            return  indent+" ".join(prod)+"\n"
        return "".join([
            "{}{}\n".format(indent,item) if isinstance(item,str)
            else "{indent}{head}(\n{body}{indent})\n".format(
                indent=indent,
                head=item[0].head,
                body=(indent+"|\n").join([
                    "{indent}#{ruleno}{cost}{feat}\n{body}".format(
                        indent=indent,
                        ruleno=alt.ruleno,
                        feat=format_feat(alt.feat),
                        body = alt.pformat_ext(level+1),
                        cost = "{%d}" % alt.cost if alt.cost!=0 else ""
                    )
                    for alt in item
                ])    
            )
            for item in prod
        ])

    def pformatr_ext(self,level=0):
        """ return prety formatted (indented multiline) string representation of right tree with extended information(rule no, feature list, cost) """
        indent = self.indenter*level
        prod = self.right
        if len(prod)==0: # empty production
            return ""
        if all(map(lambda x:isinstance(x,str),prod)): # terminal-only production
            return  indent+" ".join(prod)+"\n"
        return "".join([
            "{}{}\n".format(indent,item) if isinstance(item,str)
            else "{indent}{head}(\n{body}{indent})\n".format(
                indent=indent,
                head=item[0].head,
                body=(indent+"|\n").join([
                    "{indent}#{ruleno}{cost}{feat}\n{body}".format(
                        indent=indent,
                        ruleno=alt.ruleno,
                        feat=format_feat(alt.feat),
                        body = alt.pformatr_ext(level+1),
                        cost = "{%d}" % alt.cost if alt.cost!=0 else ""
                    )
                    for alt in item
                ])    
            )
            for item in prod
        ])

    def pformat_dbg(self,level=0):
        """ similar to pformat_ext, additionally prints globally unique ids for tree nodes """
        indent = self.indenter*level
        prod = self.left
        if len(prod)==0: # empty production
            return ""
        if all(map(lambda x:isinstance(x,str),prod)): # terminal-only production
            return  indent+" ".join(prod)+"\n"
        return "".join([
            "{}{}\n".format(indent,item) if isinstance(item,str)
            else "{indent}{head}({id})(\n{body}{indent})\n".format(
                indent=indent,
                head=item[0].head,
                id=uid(item),
                body=(indent+"|\n").join([
                    "{indent}#{ruleno}{cost}{feat}({id})\n{body}".format(
                        indent=indent,
                        ruleno=alt.ruleno,
                        feat=format_feat(alt.feat),
                        id=uid(alt),
                        body = alt.pformat_dbg(level+1),
                        cost = "{%d}" % alt.cost if alt.cost!=0 else ""
                    )
                    for alt in item
                ])    
            )
            for item in prod
        ])

    def pformatr_dbg(self,level=0):
        """ similar to pformat_ext, additionally prints globally unique ids for tree nodes """
        indent = self.indenter*level
        prod = self.right
        if len(prod)==0: # empty production
            return ""
        if all(map(lambda x:isinstance(x,str),prod)): # terminal-only production
            return  indent+" ".join(prod)+"\n"
        return "".join([
            "{}{}\n".format(indent,item) if isinstance(item,str)
            else "{indent}{head}({id})(\n{body}{indent})\n".format(
                indent=indent,
                head=item[0].head,
                id=uid(item),
                body=(indent+"|\n").join([
                    "{indent}#{ruleno}{cost}{feat}({id})\n{body}".format(
                        indent=indent,
                        ruleno=alt.ruleno,
                        feat=format_feat(alt.feat),
                        id=uid(alt),
                        body = alt.pformatr_dbg(level+1),
                        cost = "{%d}" % alt.cost if alt.cost!=0 else ""
                    )
                    for alt in item
                ])    
            )
            for item in prod
        ])
    
    formats = {
        'f' : format,
        'fr': formatr,
        'p' : pformat,
        'pr': pformatr,
        'x' : pformat_ext,
        'xr': pformatr_ext,
        'l' : list_format,
        'lr': list_formatr,
        's' : str_format,
        'sr': str_formatr,
        }

    def __format__(self,format_spec):
        return self.formats[format_spec](self)

    def __repr__(self):
        return "(head=%r,ruleno=%r,left=%r,right=%r,feat=%r,cost=%r" % (self.head,self.ruleno,self.left,self.right,self.feat,self.cost)
      
    def enum(tree,idx=0):
        """ a generator for enumerating all translations in a parse forest """
        try:
            item = tree.right[idx]
        except IndexError:
            yield ""
            return
        for rest in tree.enum(idx+1):
            if isinstance(item, str):
                if rest:
                    yield item + " " + rest
                else:
                    yield item
            else:
                for alt in item:
                    for first in alt.enum():
                        if first and rest:
                            yield first + " " + rest
                        else:
                            yield first or rest

    def enumx(tree,idx=0):
        """ a generator for enumerating all translations in a parse forest WITH corresponding costs """
        try:
            item = tree.right[idx]
        except IndexError:
            yield "",tree.cost
            return
        for rest,cost in tree.enumx(idx+1):
            if isinstance(item, str):
                if rest:
                    yield item + " " + rest, cost
                else:
                    yield item,cost
            else:
                for alt in item:
                    for first,fcost in alt.enumx():
                        if first and rest:
                            yield first + " " + rest, cost+fcost+1 # 1 for penalizing deep trees
                        else:
                            yield first or rest, cost+fcost+1 # 1 for penalizing deep trees

    #def enum_results(nodes):
    #    results = []
    #    stack = []
    #    out = []
    #    stack.append((nodes,0))
    #    backtrack = []
    #    backtrack.append((stack,out))
    #    while backtrack:
    #        stack, out = backtrack.pop()
    #        while stack:
    #            nodes, pos = stack.pop()
    #            while pos < len(nodes):
    #                node = nodes[pos]
    #                pos += 1
    #                if type(node) == str:
    #                    out.append(node)
    #                else:
    #                    stack.append((nodes,pos))
    #                    for alt in node[1:]:
    #                        alt_stack = stack.copy()
    #                        alt_stack.append((alt,0))
    #                        backtrack.append((alt_stack,out.copy()))
    #                    nodes = node[0]
    #                    pos = 0
    #        results.append(out)
    #    return results

