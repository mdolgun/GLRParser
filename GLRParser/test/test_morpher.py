import sys, unittest
sys.path.append("..")
from morpher import TurkishPostProcessor


'''
class XTestResult(unittest.TestResult):
    def addSubTest(self, test, subtest, outcome):
        # handle failures calling base class
        super(XTestResult, self).addSubTest(test, subtest, outcome)
        # add to total number of tests run
        self.testsRun += 1
'''

class TestMorpher(unittest.TestCase):
    cases = [
        ('ev-Hm', 'evim'),
        ('ev-YHm', 'evim'),
        ('ev-YdHm', 'evdim'),
        ('ev-YH', 'evi'),
        ('ev-YlA', 'evle'),
        ('ev-dA', 'evde'),
        ('ev-NHn', 'evin'),
        ('ev-ZHN', 'evi'),
        ('ev-ZHN-YH', 'evini'),
        ('ev-ZHN-YlA', 'eviyle'),
        ('ev-ZHN-dA', 'evinde'),
        ('ev-ZHN-NHn', 'evinin'),
        ('araba-Hm', 'arabam'),
        ('araba-YHm', 'arabayım'),
        ('araba-YdHm', 'arabaydım'),
        ('araba-YH', 'arabayı'),
        ('araba-YlA', 'arabayla'),
        ('araba-dA', 'arabada'),
        ('araba-NHn', 'arabanın'),
        ('araba-ZHN', 'arabası'),
        ('araba-ZHN-YH', 'arabasını'),
        ('araba-ZHN-YlA', 'arabasıyla'),
        ('araba-ZHN-dA', 'arabasında'),
        ('araba-ZHN-NHn', 'arabasının'),
        ('kitap-Hm', 'kitabım'),
        ('kitap-YHm', 'kitabım'),
        ('kitap-YdHm', 'kitaptım'),
        ('kitap-YH', 'kitabı'),
        ('kitap-YlA', 'kitapla'),
        ('kitap-dA', 'kitapta'),
        ('kitap-NHn', 'kitabın'),
        ('kitap-ZHN', 'kitabı'),
        ('kitap-ZHN-YH', 'kitabını'),
        ('kitap-ZHN-YlA', 'kitabıyla'),
        ('kitap-ZHN-dA', 'kitabında'),
        ('kitap-ZHN-NHn', 'kitabının'),
        ('hak+-Hm', 'hakkım'),
        ('hak+-YHm', 'hakkım'),
        ('hak+-YdHm', 'haktım'),
        ('hak+-YH', 'hakkı'),
        ('hak+-YlA', 'hakla'),
        ('hak+-dA', 'hakta'),
        ('hak+-NHn', 'hakkın'),
        ('hak+-ZHN', 'hakkı'),
        ('hak+-ZHN-YH', 'hakkını'),
        ('hak+-ZHN-YlA', 'hakkıyla'),
        ('hak+-ZHN-dA', 'hakkında'),
        ('hak+-ZHN-NHn', 'hakkının'),
        ('tank!-Hm', 'tankım'),
        ('tank!-YHm', 'tankım'),
        ('tank!-YdHm', 'tanktım'),
        ('tank!-YH', 'tankı'),
        ('tank!-YlA', 'tankla'),
        ('tank!-dA', 'tankta'),
        ('tank!-NHn', 'tankın'),
        ('tank!-ZHN', 'tankı'),
        ('tank!-ZHN-YH', 'tankını'),
        ('tank!-ZHN-YlA', 'tankıyla'),
        ('tank!-ZHN-dA', 'tankında'),
        ('tank!-ZHN-NHn', 'tankının'),
        ('yatak-Hm', 'yatağım'),
        ('yatak-YHm', 'yatağım'),
        ('yatak-YdHm', 'yataktım'),
        ('yatak-YH', 'yatağı'),
        ('yatak-YlA', 'yatakla'),
        ('yatak-dA', 'yatakta'),
        ('yatak-NHn', 'yatağın'),
        ('yatak-ZHN', 'yatağı'),
        ('yatak-ZHN-YH', 'yatağını'),
        ('yatak-ZHN-YlA', 'yatağıyla'),
        ('yatak-ZHN-dA', 'yatağında'),
        ('yatak-ZHN-NHn', 'yatağının'),
        ('bur@un-Hm', 'burnum'),
        ('bur@un-YHm', 'burnum'), # ??
        ('bur@un-YdHm', 'burundum'),
        ('bur@un-YH', 'burnu'),
        ('bur@un-YlA', 'burunla'),
        ('bur@un-dA', 'burunda'),
        ('bur@un-NHn', 'burnun'),
        ('bur@un-ZHN', 'burnu'),
        ('bur@un-ZHN-YH', 'burnunu'),
        ('bur@un-ZHN-YlA', 'burnuyla'),
        ('bur@un-ZHN-dA', 'burnunda'),
        ('bur@un-ZHN-NHn', 'burnunun'),
        ('renk-Hm', 'rengim'),
        ('renk-YHm', 'rengim'),
        ('renk-YdHm', 'renktim'),
        ('renk-YH', 'rengi'),
        ('renk-YlA', 'renkle'),
        ('renk-dA', 'renkte'),
        ('renk-NHn', 'rengin'),
        ('renk-ZHN', 'rengi'),
        ('renk-ZHN-YH', 'rengini'),
        ('renk-ZHN-YlA', 'rengiyle'),
        ('renk-ZHN-dA', 'renginde'),
        ('renk-ZHN-NHn', 'renginin'),
        ('ro^l-Hm', 'rolüm'),
        ('ro^l-YHm', 'rolüm'),
        ('ro^l-YdHm', 'roldüm'),
        ('ro^l-YH', 'rolü'),
        ('ro^l-YlA', 'rolle'),
        ('ro^l-dA', 'rolde'),
        ('ro^l-NHn', 'rolün'),
        ('ro^l-ZHN', 'rolü'),
        ('ro^l-ZHN-YH', 'rolünü'),
        ('ro^l-ZHN-YlA', 'rolüyle'),
        ('ro^l-ZHN-dA', 'rolünde'),
        ('ro^l-ZHN-NHn', 'rolünün'),
        ('gel-dH-m', 'geldim'),
        ('gel-dH-n', 'geldin'),
        ('gel-dH-k', 'geldik'),
        ('gel-dH-nHz', 'geldiniz'),
        ('gel-Hyor-Hm', 'geliyorum'),
        ('gel-Hyor-sHn', 'geliyorsun'),
        ('gel-Hyor-Hz', 'geliyoruz'),
        ('gel-Hyor-sHnHz', 'geliyorsunuz'),
        ('gel-YAcAk-Hm', 'geleceğim'),
        ('gel-YAcAk-sHn', 'geleceksin'),
        ('gel-YAcAk-Hz', 'geleceğiz'),
        ('gel-YAcAk-sHnHz', 'geleceksiniz'),
        ('git-dH-m', 'gittim'),
        ('git-dH-n', 'gittin'),
        ('git-dH-k', 'gittik'),
        ('git-dH-nHz', 'gittiniz'),
        ('git-Hyor-Hm', 'gidiyorum'),
        ('git-Hyor-sHn', 'gidiyorsun'),
        ('git-Hyor-Hz', 'gidiyoruz'),
        ('git-Hyor-sHnHz', 'gidiyorsunuz'),
        ('git-YAcAk-Hm', 'gideceğim'),
        ('git-YAcAk-sHn', 'gideceksin'),
        ('git-YAcAk-Hz', 'gideceğiz'),
        ('git-YAcAk-sHnHz', 'gideceksiniz'),
        ('oku-dH-m', 'okudum'),
        ('oku-dH-n', 'okudun'),
        ('oku-dH-k', 'okuduk'),
        ('oku-dH-nHz', 'okudunuz'),
        ('oku-Hyor-Hm', 'okuyorum'),
        ('oku-Hyor-sHn', 'okuyorsun'),
        ('oku-Hyor-Hz', 'okuyoruz'),
        ('oku-Hyor-sHnHz', 'okuyorsunuz'),
        ('oku-YAcAk-Hm', 'okuyacağım'),
        ('oku-YAcAk-sHn', 'okuyacaksın'),
        ('oku-YAcAk-Hz', 'okuyacağız'),
        ('oku-YAcAk-sHnHz', 'okuyacaksınız'),
        ('ara-dH-m', 'aradım'),
        ('ara-dH-n', 'aradın'),
        ('ara-dH-k', 'aradık'),
        ('ara-dH-nHz', 'aradınız'),
        ('ara-Hyor-Hm', 'arıyorum'),
        ('ara-Hyor-sHn', 'arıyorsun'),
        ('ara-Hyor-Hz', 'arıyoruz'),
        ('ara-Hyor-sHnHz', 'arıyorsunuz'),
        ('ara-YAcAk-Hm', 'arayacağım'),
        ('ara-YAcAk-sHn', 'arayacaksın'),
        ('ara-YAcAk-Hz', 'arayacağız'),
        ('ara-YAcAk-sHnHz', 'arayacaksınız'),
        ('git-mA-Hm', 'gitmem'),
        ('üst! -Hm', 'üstüm'),
    ]
    '''
    def run(self, test_result=None):
        return super(TestMorph, self).run(XTestResult())
    '''
    def setUp(self):
        self.processor = TurkishPostProcessor()

    def test_all(self):
        for sent,out in self.cases:
            with self.subTest(sent=sent,out=out):
                self.assertEqual(self.processor(sent),out)
                     
def main():
    # used for data generation
    morpher = TurkishPostProcessor()
    data = []

    words = [ "ev", "araba", "kitap", "hak+", "tank!", "yatak", "bur@un", "renk", "ro^l" ]
    suffixes = [ "-Hm", "-YHm", "-YdHm", "-YH", "-YlA", "-dA", "-NHn", "-ZHN", "-ZHN-YH", "-ZHN-YlA", "-ZHN-dA", "-ZHN-NHn" ]

    for word in words:
        for suffix in suffixes:
            nword = word + suffix
            data.append((nword, morpher(nword)))

    words = [ "gel", "git", "oku", "ara" ]
    suffixes = [ "-dH-m", "-dH-n", "-dH-k", "-dH-nHz", "-Hyor-Hm", "-Hyor-sHn", "-Hyor-Hz", "-Hyor-sHnHz", "-YAcAk-Hm", "-YAcAk-sHn", "-YAcAk-Hz", "-YAcAk-sHnHz" ]

    for word in words:
        for suffix in suffixes:
            nword = word + suffix
            data.append((nword, morpher(nword)))
    for item in data:
        print(item,",",sep="")   

if __name__== '__main__':
    unittest.main()
    #main()