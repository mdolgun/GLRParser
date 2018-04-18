""" A GLR Parser for Natural Language Processing and Translation

(c) 2018 by Mehmet Dolgun, m.dolgun@yahoo.com

This file define classes:
    Tree: node of a parse tree
      
"""
if len(__name__.split("."))>1: # called within a package
    from .grammar import format_feat
else: # called as a module or script
    from grammar import format_feat

empty_dict = dict()
empty_list = list()

uid_dict = dict()
uid_cnt = 0
def uid(obj):
    global uid_cnt, uid_dict
    _id = id(obj)
    if _id in uid_dict:
        return uid_dict[_id]
    uid_cnt += 1
    uid_dict[_id] = uid_cnt
    return uid_cnt


class Tree:
    __slots__ = ('head', 'ruleno', 'left', 'right', 'feat', 'cost')
    def __init__(self, head, ruleno, left=empty_list, right=empty_list, feat=empty_dict, cost=0):
        self.head = head
        self.ruleno = ruleno
        self.left = left
        self.right = right
        self.feat = feat
        self.cost = cost

    def format(self,tree_type=True):
        """ returnes single-line formatted string representation of a tree """
        return " ".join([
            item if type(item)==str
            else "{}({})".format(item[0].head,"|".join([alt.format(tree_type) for alt in item]))
            for item in (self.left if tree_type else self.right)
            ])

    def str_format(self,tree_type=True):
        """ return string representation of terminals where alternative strings are in the form: (alt1|alt2|...) """
        return " ".join([
            item if type(item)==str 
            else item[0].str_format(tree_type) if len(item)==1
            else "("+"|".join([alt.str_format(tree_type) for alt in item])+")"
            for item in (self.left if tree_type else self.right)
        ])
    """
    def convert(self):   
        return " ".join([
            item if type(item)==str 
            else "("+"|".join([convert_tree(alt) for alt in item])+")"
            for item in self
        ])
    """

    def list_format(self,tree_type=True):
        out = []
        for item in (self.left if tree_type else self.right):
            if type(item)==str:
                out.append(item)
            elif len(item)==1:
                out.extend(item[0].list_format(tree_type))
            else:
                out.append([alt.list_format(tree_type) for alt in item])
        return out

    indenter = "    "
    def pformat(self,tree_type=True,level=0):
        """ return prety formatted (indented multiline) string representation of a tree """
        indent = self.indenter*level
        return "".join([
            "{}{}\n".format(indent,item) if type(item)==str
            else "{indent}{head}({body})\n".format(
                indent=indent,
                head=item[0].head,
                body=" ".join(item[0].left if tree_type else item[0].right)    
            ) if len(item)==1 and all(map(lambda x:type(x)==str,(item[0].left if tree_type else item[0].right)))
            else "{indent}{head}(\n{body}{indent})\n".format(
                indent=indent,
                head=item[0].head,
                body=(indent+"|\n").join([alt.pformat(tree_type,level+1) for alt in item])  
            )
            for item in (self.left if tree_type else self.right)
        ])

    def pformat_ext(self,tree_type=True,level=0):
        """ return prety formatted (indented multiline) string representation of a tree with extended information(rule no, feature list, cost) """
        indent = self.indenter*level
        prod = self.left if tree_type else self.right
        if len(prod)==0: # empty production
            return ""
        if all(map(lambda x:type(x)==str,prod)): # terminal-only production
            return  indent+" ".join(prod)+"\n"
        return "".join([
            "{}{}\n".format(indent,item) if type(item)==str
            else "{indent}{head}(\n{body}{indent})\n".format(
                indent=indent,
                head=item[0].head,
                body=(indent+"|\n").join([
                    "{indent}#{ruleno}{cost}{feat}\n{body}".format(
                        indent=indent,
                        ruleno=alt.ruleno,
                        feat=format_feat(alt.feat),
                        body = alt.pformat_ext(tree_type,level+1),
                        cost = "{%d}" % alt.cost if alt.cost!=0 else ""
                    )
                    for alt in item
                ])    
            )
            for item in prod
        ])

    def pformat_dbg(self,tree_type=True,level=0):
        """ return prety formatted (indented multiline) string representation of a tree with extended information(rule no, feature list, cost) """
        indent = self.indenter*level
        prod = self.left if tree_type else self.right
        if len(prod)==0: # empty production
            return ""
        if all(map(lambda x:type(x)==str,prod)): # terminal-only production
            return  indent+" ".join(prod)+"\n"
        return "".join([
            "{}{}\n".format(indent,item) if type(item)==str
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
                        body = alt.pformat_dbg(tree_type,level+1),
                        cost = "{%d}" % alt.cost if alt.cost!=0 else ""
                    )
                    for alt in item
                ])    
            )
            for item in prod
        ])
    def formatr(self):
        return self.format(False)

    def pformatr(self):
        return self.pformat(False)

    def pformatr_ext(self):
        return self.pformat_ext(False)

    def pformatr_dbg(self):
        return self.pformat_dbg(False)

    def list_formatr(self):
        return self.list_format(False)

    def str_formatr(self):
        return self.str_format(False)
    
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
            if type(item)==str:
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
            if type(item)==str:
                if rest:
                    yield item + " " + rest, cost
                else:
                    yield item,cost
            else:
                for alt in item:
                    for first,fcost in alt.enumx():
                        if first and rest:
                            yield first + " " + rest, cost+fcost
                        else:
                            yield first or rest, cost+fcost

