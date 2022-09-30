GLRParser
=========

A GLR Parser for Natural Language Processing and Translation

GLRParser is not just a parser. It's

* Natural Language Parser which handles ambiguous grammars
* Unification Engine which handles unification of features
* Translation Engine for Syntax-Based Translation of Natural Languages

For a quick start, you can use following commands to install and run an interactive demo for English to Turkish Translation:

::

	pip install GLRParser
	python -m GLRParser.main
	
In interactive demo, you can enter an English sentence to get Turkish translation(s):

::

	Grammar load time: 806,295 mics
	Number of rules: 24915
	Number of states: 28047
	Number of symbols: 5738
	Number of NonTerm symbols: 159
	Enter Sent> who do you think you are
	  kim olduğunuzu düşünüyorsunuz
	Enter Sent> as long as she is happy i will be happy
	  mutlu olduğu sürece mutlu olacağım
	Enter Sent> his sudden departure had demonstrated how unreliable he was
	  ani ayrılışı ne kadar güvenilmez olduğunu göstermişti
	Enter Sent> attacks were threatening to destabilize the government
	  saldırılar yönetimi istikrarsızlaştırmakla tehdit ediyordu
	Enter Sent> if i had come early she wouldn't have missed her bus
	  erken gelmiş olsaydım otobüsünü kaçırmış olmazdı
	  erken gelmiş olsaydım otobüsünü özlemiş olmazdı
	
You can also visit following url to try interactive translations: https://mdolgun.pythonanywhere.com/

For a list of sample translations check the file: https://github.com/mdolgun/GLRParser/blob/master/GLRParser/grm/main.out.txt

For detailed information about the features and the grammar syntax, you can refer to wiki page: https://github.com/mdolgun/GLRParser/wiki

Sample code for parsing and translation should be like:

.. code:: python

	from GLRParser import Parser, ParseError, GrammarError, Tree

	try:
		parser = Parser() # initialize parser object

		parser.parse_grammar("GLRParser\grm\simple_trans.grm") # load grammar from a file
		sent = "i saw the man in the house with the telescope" # sentence to parse

		parser.compile() # constructs parsing tables
		parser.parse(sent) # parse the sentence

		tree = parser.make_tree() # generates parse forest
		ttree = parser.trans_tree(tree) # translate the parse forest

		print(ttree.pformatr()) # pretty-print the translated parse forest

		for trans in ttree.enum(): # enumerate and print all alternative translations in the parse forest
			print(trans.replace(" -","")) # concat suffixes
	except GrammarError as ge:
		print(ge)
	except ParseError as pe:
		print(pe))

Simple grammar for English -> Turkish translation (see simple_trans.grm)

::

        S -> NP VP : NP VP
        S -> S in NP : NP -de S 
        S -> S with NP : NP -la S 
        NP -> i : 
        NP -> the man : adam
        NP -> the telescope : teleskop
        NP -> the house : ev
        NP -> NP-1 in NP-2 : NP-2 -deki NP-1
        NP -> NP-1 with NP-2 : NP-2 -lu NP-1
        VP -> saw NP : NP -ı gördüm  

Given the above grammar and input string:

::

    i saw the man in the house with the telescope

It produces a parse forest, and 5 alternative translations (of
which two are identical):

::

    1. teleskopla evde adamı gördüm
    2. teleskopla evdeki adamı gördüm
    3. teleskoplu evde adamı gördüm
    4. teleskoplu evdeki adamı gördüm
    5. teleskoplu evdeki adamı gördüm

The semantic interpretations are:

::

    1. saw(in the house) saw(with the telescope)
    2. man(in the house) saw(with the telescope) 
    3. saw(in the house) house(with the telescope)
    4. man(in the house) man(with the telescope)
    5. man(in the house) house(with the telescope)
