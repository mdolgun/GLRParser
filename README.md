# GLRParser
A GLR Parser for Natural Language Processing and Translation  

All functionality is provided by main class: Parser  
The input grammar should be a list of rules in the form:  
    NonTerminal "->" (SourceTerminal|NonTerminal)* ":" (DestTerminal|NonTerminal)*  
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

ToDo:  
    1. Morphological Processing  
    2. Feature sets  
    3. Interactive GUI  
    4. A better grammar parser  
    5. Dictionary  
