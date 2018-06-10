""" Morphological Post-Processing for Turkish

(c) 2018 by Mehmet Dolgun, m.dolgun@yahoo.com

All functionality is provided by main class: TurkishPostProcessor

    special characters
    Vowel Harmony:
    ^ : make previous vowel back, i.e. aIuo->eiUO e.g kol-A -> kola, ro^l-A -> role
    H : high vowels, using harmony rules aI->I, ei->i, uo->u, UO->U  e.g ev-Hm -> evim, yol-Hm -> yolum
    A : low,unrounded vowels, using harmony rules aIuo->a, eiUO->e e.g. ev-lAr -> evler yol-lAr -> yollar
    Consonants
    N : used as last char of same suffixes (e.g. 3d sing possesive), realized to n only if it is followed by a vowel e.g. tereyağıN-ı->tereyağını, tereyağıN-ım ->tereyağım
    @ : drops the next vowel if it takes a vowel-starting suffix e.g. bur@un-u -> burnu, bur@un-da -> burunda
    + : duplicates previous letter if it takes a vowel-starting suffix e.g. hak+-ı -> hakkı, hak+-ta -> hakta
    ! : prevents softening of previous consonant e.g. kitap-ı -> kitabı, hap!-ı -> hapı
	
	Note that ^, $, +, !, N symbols is used only in word root, N is required for compound nouns

"""

import re

class PostProcessError(Exception):
    """ Raised when a suffix cannot be applied to word stem """
    pass

class TurkishPostProcessor:
    """
    rules = [
        ( "(?<=[aIeiouOU]-)(H)" , "" ),
        ( "(?<=[^aIeiouOU]-)([nsy])", "" ),
        ( "(N-y)(?=[aIeiouOUHA])", "n" ),
        ( "(N-y)(?=[^aIeiouOUHA])", "y" ),
        ( "([pCtk])-(?=[snHA]|y[aIeiouOUHA])", {'p':'b', 'C':'c', 't':'d', 'k':'G'} ),
        ( "([pbctdk]\+)-(?=[snHA]|y[aIeiouOUHA])", {'p+':'bb', 'b+':'bb', 'c+':'cc', 't+':'tt', 'd+':'dd', 'k+':'kk' } ),
        ( "(\$[IiuU])(?=[^aIeiouOU]-(?:[snHA]|y[aIeiouOUHA]))", ""),
        ( "(enk)-(?=[snHA]|y[aIeiouOUHA])", "eng"),
        ( "(N)-", "n"),
        ( "(?<=[pCtkSfsh]-)(Y?d)","t"),
        ( "(?<=[pCtkSfsh][\+!]-)(Y?d)","t"),
        ( "([-\$\+!]|N$)", "")
    ]
    """
    rules = [
        ( "(?<=[pCtkSfsh]-)(Y?d)","t"),
        ( "(?<=[pCtkSfsh][\+!]-)(Y?d)","t"),
        ( "(@[IiuU])(?=[^aIeiouOU]-(?:[ZNHA]|Y[aIeiouOUHA]))", ""),
        ( "([aIeiouOUA]-H)(?=yor)" , "H" ),
        ( "(?<=[aIeiouOU]-)(H)" , "" ),
        ( "(?<=[^aIeiouOUAH]-)([NZY])" , "" ),
        ( "(?<=[aIeiouOUAH]-)([NZY])", {'N':'n', 'Z':'s', 'Y':'y'} ),
        ( "(N-Y)(?=[^aIeiouOUAH])", "y" ),
        ( "(N-Y)(?=[AH])", "n" ),
        ( "(N)-(?=[^Y])", "n"),
        ( "(enk)-(?=[ZNHA]|Y[aIeiouOUHA])", "eng"),
        ( "([pCtk])-(?=[ZNHA]|Y[aIeiouOUHA])", {'p':'b', 'C':'c', 't':'d', 'k':'G'} ),
        ( "([pbctdk]\+)-(?=[ZNHA]|Y[aIeiouOUHA])", {'p+':'bb', 'b+':'bb', 'c+':'cc', 't+':'tt', 'd+':'dd', 'k+':'kk' } ),
        ( "([-@\+!]|N$|N(?= ))", "")
    ]

    vowel = { 'a': 0, 'I':0 , 'e':1, 'i':1, 'o':2, 'u':2 , 'O':3, 'U':3 }
    H = [ 'I', 'i', 'u', 'U' ]
    A = [ 'a', 'e', 'a', 'e' ]

    outtab = { 71:'ğ', 85:'ü', 79:'ö', 67:'ç', 83:'ş', 73:'ı' } # internal to unicode
    #outtab = { 71:'ð', 85:'ü', 79:'ö', 67:'ç', 83:'þ', 73:'ý' } # internal to codepage 
    intab  = { # to internal
        252:'U', 220:'U', 246:'O', 214:'O', 231:'C', 199:'C', # from common unicode & codepage
        240:'G', 208:'G', 222:'S', 222:'S', 253:'I', 221:'i', # from code page 
        287:'G', 286:'G', 351:'S', 350:'S', 305:'I', 304:'i'  # from unicode 
    }    
    def __init__(self):
        relist, self.replist = zip(*TurkishPostProcessor.rules)
        self.rx = re.compile('|'.join(relist))
        
    def handle_match(self,match):
        for idx,val in enumerate(match.groups()):
            if val:
                repl = self.replist[idx]
                if type(repl) == dict:
                    return repl[val]
                else:
                    return repl
            
    def vowel_harmony(word):
        voweltype = 0
        out = []
        for char in word:
            if char in TurkishPostProcessor.vowel:
                voweltype = TurkishPostProcessor.vowel[char]
            elif char == 'H':
                char = TurkishPostProcessor.H[voweltype]
            elif char == 'A':
                char = TurkishPostProcessor.A[voweltype]
                voweltype &= 1
            elif char == '^':
                voweltype |= 1
                continue
            out.append(char)
        return "".join(out)
    
    
    def __call__(self,text):
        #print(text)
        items = text.split()
        for idx,item in enumerate(items):
            if item == "+copy":
                back_word = items[idx-1]
                del items[idx]
            elif item == "+paste":
                items[idx] = back_word
            elif item.startswith("+"):
                dicidx,sufidx = self.suff_idxs[item[1:]]
                prev = items[idx-1]
                try:
                    items[idx-1] = self.suff_dict_list[dicidx][prev][sufidx]
                except KeyError:
                    raise PostProcessError("Postprocess Error: sent: %s word: %s, suffix: %s" % (text, prev,item))
                del items[idx]
        text = " ".join(items)

        return TurkishPostProcessor.vowel_harmony(
            self.rx.sub(
                self.handle_match,
                text.replace(' -','-').translate(self.intab)
            )
        ).translate(self.outtab)

def main():
    morpher = TurkishPostProcessor()

    words = [ "ev", "araba", "kitap", "hak+", "tank!", "yatak", "bur@un", "renk", "ro^l" ]
    suffixes = [ "-Hm", "-YHm", "-YdHm", "-YH", "-YlA", "-dA", "-NHn", "-ZHN", "-ZHN-YH", "-ZHN-YlA", "-ZHN-dA", "-ZHN-NHn" ]

    for word in words:
        for suffix in suffixes:
            nword = word + suffix
            print(nword, morpher(nword))

    words = [ "gel", "git", "oku", "ara" ]
    suffixes = [ "-dH-m", "-dH-n", "-dH-k", "-dH-nHz", "-Hyor-YHm", "-Hyor-sHn", "-Hyor-YHz", "-Hyor-sHnHz", "-YAcAk-YHm", "-YAcAk-sHn", "-YAcAk-YHz", "-YAcAk-sHnHz", "-mAlH-YHm", "-mAlH-sHn", "-mAlH-YHz", "-mAlH-sHnHz" ]

    for word in words:
        for suffix in suffixes:
            nword = word + suffix
            print(nword, morpher(nword))

if __name__ == "__main__":
    # execute only if run as a script
    main()

