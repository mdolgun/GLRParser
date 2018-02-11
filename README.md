# GLRParser
A GLR Parser for Natural Language Processing and Translation  

All functionality is provided by main class: `Parser`  
The input grammar should be a list of rules in the form:  
```
    NonTerminal "->" (SourceTerminal|NonTerminal)* [ ":" (DestTerminal|NonTerminal) ] [ # comment ]
```
empty lines and any characters after "#" are ignored 

Sample usage of the Parser class should be like:

```
    parser = Parser()
    try:
        parser.load_grammar("sample.grm")
        sent = "i saw the man in the house with the telescope"

        parser.compile()
        parser.parse(sent)
        tree = parser.make_tree()
        ttree = parser.trans_tree(tree)

        for no,alt in enumerate(Parser.gen_tree(ttree)):
            print(no+1,alt.replace(" -",""))
    except ParseError as pe:
        print(pe.args)
    except GrammarError as ge:
        print(ge.args)
```

Sample grammar for English -> Turkish translation (see sample.grm) 
```
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
```

Given the above grammar and input string:
```
i saw the man in the house with the telescope
```

It produces 5 alternative parse trees and 5 alternative translations (of which two are identical):
```
1 adamı gördüm evde teleskopla
2 evdeki adamı gördüm teleskopla
3 adamı gördüm teleskoplu evde
4 teleskoplu evdeki adamı gördüm
5 teleskoplu evdeki adamı gördüm
```
The semantic interpretations are:
```
1. saw(in the house) saw(with the telescope)
2. man(in the house) saw(with telescope) 
3. saw(in the house) house(with the telescope)
4. man(in the house) man(with telescope)
5. man(in the house) house(with the telescope)
```    
ToDo:  
    1. Morphological Processing  
    2. Feature sets  
    3. Interactive GUI  
    4. A better grammar parser  
    5. Dictionary  
