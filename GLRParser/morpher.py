""" Morphological Post-Processing for Turkish

(c) 2018 by Mehmet Dolgun, m.dolgun@yahoo.com

All functionality is provided by main class: TurkishPostProcessor

    special characters
    Vowel Harmony:
    ^ : make previous vowel back, i.e. aIuo->eiUO e.g kol-A -> kola, rol^-A -> role
    H : high vowels, using harmony rules aI->I, ei->i, uo->u, UO->U  e.g ev-Hm -> evim, yol-Hm -> yolum
    A : low,unrounded vowels, using harmony rules aIuo->a, eiUO->e e.g. ev-lAr -> evler yol-lAr -> yollar
    Consonants
    N : used as last char of same suffixes (e.g. 3d sing possesive), realized to n only if it is followed by a vowel e.g. tereyağıN-ı->tereyağını, tereyağıN-ım ->tereyağım
    @ : drops the next vowel if it takes a vowel-starting suffix e.g. bur@un-u -> burnu, bur@un-da -> burunda
    + : duplicates previous letter if it takes a vowel-starting suffix e.g. hak+-ı -> hakkı, hak+-ta -> hakta
    ? : soften previous consonant e.g. kitap?-ı -> kitabı, hap-ı -> hapı
	
	Note that ^, $, +, ?, N symbols is used only in word root, N is required for compound nouns

"""

import re

class PostProcessError(Exception):
    """ Raised when a suffix cannot be applied to word stem """
    pass

class TurkishPostProcessor:
    rules = [
        ( "(y\?)(?=[ZNHAY])", "y"),                  # su[y?]ZHN=>su[y]ZHN, su[y?]NHn=>su[y]NHn, su[y?]Hm=>su[y]um
        ( "(nk\?)(?=[ZNHA]|Y[aIeiouOUHA])", "ng"),  # re[nk?]ZHN=>re[ng]i, re[nk?]NHn=>re[ng]in, re[nk?]Hm=>re[ng]im, re[nk?]YA=>re[ng]e
        ( "([pCtk]\?)(?=[ZNHAV]|Y[aIeiouOUHA])", {'p?':'b', 'C?':'c', 't?':'d', 'k?':'G'} ), # kita[p?]ZHN=>kita[b]ZHN, kita[p?]NHn=>kita[b]NHn, kita[p?]Hm=>kita[b]Hm, kita[p?]YA=>kita[b]?YA
        ( "(?<=[pCtkSfsh])([?+^]?Y?D)","t"),         # ip[D]A=>ipte, ip[YD]H=>ipti, kitap[?D]A=>kitapta, kitap[?YD]H=>kitaptı, hak[+D]A=>hakta, hak[+YD]H=>haktı
        ( "([pbctdk]\+)(?=[ZNHA]|Y[aIeiouOUHA])", {'p+':'bb', 'b+':'bb', 'c+':'cc', 't+':'tt', 'd+':'dd', 'k+':'kk' } ),
        ( "([aIeiouOUA]V)(?=yor)" , "H" ),
        ( "([VD])" , {"V":"H", "D":"d"} ),          # sev[V]yor=>sev[H]yor, ev[D]A=>ev[d]A
        ( "(y?[?+])", ""),                           # su(y?)=>su, kitap(?)=>kitap(), su(y?)DA=>su()DA, kitap(?)DA
        ( "(?<=[aIeiouOUA])(H)" , "" ),             # oda(H)m=> oda()m
        ( "(NY)(?=[^aIeiouOUAH])", "y" ),
        ( "(NY)(?=[AH])", "n" ),
        ( "(?<=[aIeiouOUAH])([NZY])(?!$| )", {'N':'n', 'Z':'s', 'Y':'y'} ), # oda[Z]HN=>oda[s]HN, oda[N]Hn=>oda[n]Hn, oda[Y]H=>oda[y]H
        ( "(@[IiuU])(?=[^aIeiouOU](?:[ZNHA]|Y[aIeiouOUHA]))", ""), # bur(@u)nZHN=>bur()nZHN, bur(@u)nNHn=>bur()nNHn, bur(@u)nHm=>bur()nHm, bur(@u)nYA=>bur()nYA
        ( "([@NZY])", "")                           # ev(Z)HN=>ev()HN, ev(N)Hn=>ev()Hn, ev(Y)H=>ev()H, bur(@)un=>bur()un
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
        previdx = None
        for idx,item in enumerate(items):
            if item == "+copy":
                back_word = items[idx-1]
                items[idx] = None
            elif item == "+paste":
                items[idx] = back_word
                previdx = idx
            elif item.startswith("+"):
                if previdx is None:
                    raise PostProcessError("sent: %s Word stem not found" % text) 
                #try:
                #    dicidx,sufidx = self.suff_idxs[item[1:]]
                #except KeyError:
                #    raise PostProcessError("Postprocess Error: sent: %s Unknown suffix: %s" % (text, item))  
                #try:
                #    prev = items[previdx]
                #    items[previdx] = self.suff_dict_list[dicidx][prev][sufidx]
                #    items[idx] = None
                #except KeyError:
                #    try:
                #        items[idx] = self.suff_dict_list[dicidx][""][sufidx]
                #    except KeyError:
                #        raise PostProcessError("Postprocess Error: sent: %s word: %s, suffix: %s" % (text, prev, item))
                try:
                    prev = items[previdx]
                    items[previdx] = self.suff_dict[prev+item]
                    items[idx] = None
                except KeyError:
                    try:
                        items[idx] = self.suff_dict[item]
                    except KeyError:
                        raise PostProcessError("sent: %s word: %s, suffix: %s" % (text, prev, item))
            else:
                previdx = idx
        text = " ".join(item for item in items if item)

        #return TurkishPostProcessor.vowel_harmony(
        #    self.rx.sub(
        #        self.handle_match,
        #        text.replace(' -','').translate(self.intab)
        #    )
        #).translate(self.outtab)
        inp = text.replace(' -','').translate(self.intab) 
        result = self.rx.sub(self.handle_match, inp)
        result = TurkishPostProcessor.vowel_harmony(result)
        result = result.translate(self.outtab).replace("' "," ")
        return result

def main():
    morpher = TurkishPostProcessor()

    words = [ "ev", "araba", "kitap?", "hak+", "tank", "yatak?", "bur@un", "renk?", "rol^", "suy?" ]
    suffixes = [ "Hm", "YH", "YlA", "DA", "NHn", "ZHN", "YDH"]

    for word in words:
        for suffix in suffixes:
            nword = word + suffix
            print(nword, morpher(nword))

    words = [ "oda" ]
    suffixes = [ "ZHNYH", "ZHNYlA", "ZHNDA", "ZHNNHn" ]
    for word in words:
        for suffix in suffixes:
            nword = word + suffix
            print(nword, morpher(nword))


    words = [ "gel", "git?", "oku", "ara" ]
    suffixes = [ "DHm", "VyorYHm", "YAcAk?YHm", "mAlHYHm", "mHşYDHm", "DHYDHm"]

    for word in words:
        for suffix in suffixes:
            nword = word + suffix
            nword = nword.replace("-","")
            print(nword, morpher(nword))


if __name__ == "__main__":
    # execute only if run as a script
    main()

