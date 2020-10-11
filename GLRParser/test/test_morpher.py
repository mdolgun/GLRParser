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
        ('ev-YDHm', 'evdim'),
        ('ev-YH', 'evi'),
        ('ev-YlA', 'evle'),
        ('ev-DA', 'evde'),
        ('ev-NHn', 'evin'),
        ('ev-ZHN', 'evi'),
        ('ev-ZHN-YH', 'evini'),
        ('ev-ZHN-YlA', 'eviyle'),
        ('ev-ZHN-DA', 'evinde'),
        ('ev-ZHN-NHn', 'evinin'),
        ('araba-Hm', 'arabam'),
        ('araba-YHm', 'arabayım'),
        ('araba-YDHm', 'arabaydım'),
        ('araba-YH', 'arabayı'),
        ('araba-YlA', 'arabayla'),
        ('araba-DA', 'arabada'),
        ('araba-NHn', 'arabanın'),
        ('araba-ZHN', 'arabası'),
        ('araba-ZHN-YH', 'arabasını'),
        ('araba-ZHN-YlA', 'arabasıyla'),
        ('araba-ZHN-DA', 'arabasında'),
        ('araba-ZHN-NHn', 'arabasının'),
        ('kitap?-Hm', 'kitabım'),
        ('kitap?-YHm', 'kitabım'),
        ('kitap?-YDHm', 'kitaptım'),
        ('kitap?-YH', 'kitabı'),
        ('kitap?-YlA', 'kitapla'),
        ('kitap?-DA', 'kitapta'),
        ('kitap?-NHn', 'kitabın'),
        ('kitap?-ZHN', 'kitabı'),
        ('kitap?-ZHN-YH', 'kitabını'),
        ('kitap?-ZHN-YlA', 'kitabıyla'),
        ('kitap?-ZHN-DA', 'kitabında'),
        ('kitap?-ZHN-NHn', 'kitabının'),
        ('hak+-Hm', 'hakkım'),
        ('hak+-YHm', 'hakkım'),
        ('hak+-YDHm', 'haktım'),
        ('hak+-YH', 'hakkı'),
        ('hak+-YlA', 'hakla'),
        ('hak+-DA', 'hakta'),
        ('hak+-NHn', 'hakkın'),
        ('hak+-ZHN', 'hakkı'),
        ('hak+-ZHN-YH', 'hakkını'),
        ('hak+-ZHN-YlA', 'hakkıyla'),
        ('hak+-ZHN-DA', 'hakkında'),
        ('hak+-ZHN-NHn', 'hakkının'),
        ('tank-Hm', 'tankım'),
        ('tank-YHm', 'tankım'),
        ('tank-YDHm', 'tanktım'),
        ('tank-YH', 'tankı'),
        ('tank-YlA', 'tankla'),
        ('tank-DA', 'tankta'),
        ('tank-NHn', 'tankın'),
        ('tank-ZHN', 'tankı'),
        ('tank-ZHN-YH', 'tankını'),
        ('tank-ZHN-YlA', 'tankıyla'),
        ('tank-ZHN-DA', 'tankında'),
        ('tank-ZHN-NHn', 'tankının'),
        ('yatak?-Hm', 'yatağım'),
        ('yatak?-YHm', 'yatağım'),
        ('yatak?-YDHm', 'yataktım'),
        ('yatak?-YH', 'yatağı'),
        ('yatak?-YlA', 'yatakla'),
        ('yatak?-DA', 'yatakta'),
        ('yatak?-NHn', 'yatağın'),
        ('yatak?-ZHN', 'yatağı'),
        ('yatak?-ZHN-YH', 'yatağını'),
        ('yatak?-ZHN-YlA', 'yatağıyla'),
        ('yatak?-ZHN-DA', 'yatağında'),
        ('yatak?-ZHN-NHn', 'yatağının'),
        ('bur@un-Hm', 'burnum'),
        ('bur@un-YHm', 'burnum'), # ??
        ('bur@un-YDHm', 'burundum'),
        ('bur@un-YH', 'burnu'),
        ('bur@un-YlA', 'burunla'),
        ('bur@un-DA', 'burunda'),
        ('bur@un-NHn', 'burnun'),
        ('bur@un-ZHN', 'burnu'),
        ('bur@un-ZHN-YH', 'burnunu'),
        ('bur@un-ZHN-YlA', 'burnuyla'),
        ('bur@un-ZHN-DA', 'burnunda'),
        ('bur@un-ZHN-NHn', 'burnunun'),
        ('renk?-Hm', 'rengim'),
        ('renk?-YHm', 'rengim'),
        ('renk?-YDHm', 'renktim'),
        ('renk?-YH', 'rengi'),
        ('renk?-YlA', 'renkle'),
        ('renk?-DA', 'renkte'),
        ('renk?-NHn', 'rengin'),
        ('renk?-ZHN', 'rengi'),
        ('renk?-ZHN-YH', 'rengini'),
        ('renk?-ZHN-YlA', 'rengiyle'),
        ('renk?-ZHN-DA', 'renginde'),
        ('renk?-ZHN-NHn', 'renginin'),
        ('rol^-Hm', 'rolüm'),
        ('rol^-YHm', 'rolüm'),
        ('rol^-YDHm', 'roldüm'),
        ('rol^-YH', 'rolü'),
        ('rol^-YlA', 'rolle'),
        ('rol^-DA', 'rolde'),
        ('rol^-NHn', 'rolün'),
        ('rol^-ZHN', 'rolü'),
        ('rol^-ZHN-YH', 'rolünü'),
        ('rol^-ZHN-YlA', 'rolüyle'),
        ('rol^-ZHN-DA', 'rolünde'),
        ('rol^-ZHN-NHn', 'rolünün'),
        ('suy?-Hm', 'suyum'),
        ('suy?-YHm', 'suyum'),
        ('suy?-YDHm', 'suydum'),
        ('suy?-YH', 'suyu'),
        ('suy?-YlA', 'suyla'),
        ('suy?-DA', 'suda'),
        ('suy?-NHn', 'suyun'),
        ('suy?-ZHN', 'suyu'),
        ('suy?-ZHN-YH', 'suyunu'),
        ('suy?-ZHN-YlA', 'suyuyla'),
        ('suy?-ZHN-DA', 'suyunda'),
        ('suy?-ZHN-NHn', 'suyunun'),
        ('gel-DH-m', 'geldim'),
        ('gel-DH-n', 'geldin'),
        ('gel-DH-k', 'geldik'),
        ('gel-DH-nHz', 'geldiniz'),
        ('gel-Vyor-Hm', 'geliyorum'),
        ('gel-Vyor-sHn', 'geliyorsun'),
        ('gel-Vyor-Hz', 'geliyoruz'),
        ('gel-Vyor-sHnHz', 'geliyorsunuz'),
        ('gel-YAcAk?-Hm', 'geleceğim'),
        ('gel-YAcAk?-sHn', 'geleceksin'),
        ('gel-YAcAk?-Hz', 'geleceğiz'),
        ('gel-YAcAk?-sHnHz', 'geleceksiniz'),
        ('git?-DH-m', 'gittim'),
        ('git?-DH-n', 'gittin'),
        ('git?-DH-k', 'gittik'),
        ('git?-DH-nHz', 'gittiniz'),
        ('git?-Vyor-Hm', 'gidiyorum'),
        ('git?-Vyor-sHn', 'gidiyorsun'),
        ('git?-Vyor-Hz', 'gidiyoruz'),
        ('git?-Vyor-sHnHz', 'gidiyorsunuz'),
        ('git?-YAcAk?-Hm', 'gideceğim'),
        ('git?-YAcAk?-sHn', 'gideceksin'),
        ('git?-YAcAk?-Hz', 'gideceğiz'),
        ('git?-YAcAk?-sHnHz', 'gideceksiniz'),
        ('oku-DH-m', 'okudum'),
        ('oku-DH-n', 'okudun'),
        ('oku-DH-k', 'okuduk'),
        ('oku-DH-nHz', 'okudunuz'),
        ('oku-Vyor-Hm', 'okuyorum'),
        ('oku-Vyor-sHn', 'okuyorsun'),
        ('oku-Vyor-Hz', 'okuyoruz'),
        ('oku-Vyor-sHnHz', 'okuyorsunuz'),
        ('oku-YAcAk?-Hm', 'okuyacağım'),
        ('oku-YAcAk?-sHn', 'okuyacaksın'),
        ('oku-YAcAk?-Hz', 'okuyacağız'),
        ('oku-YAcAk?-sHnHz', 'okuyacaksınız'),
        ('ara-DH-m', 'aradım'),
        ('ara-DH-n', 'aradın'),
        ('ara-DH-k', 'aradık'),
        ('ara-DH-nHz', 'aradınız'),
        ('ara-Vyor-Hm', 'arıyorum'),
        ('ara-Vyor-sHn', 'arıyorsun'),
        ('ara-Vyor-Hz', 'arıyoruz'),
        ('ara-Vyor-sHnHz', 'arıyorsunuz'),
        ('ara-YAcAk?-Hm', 'arayacağım'),
        ('ara-YAcAk?-sHn', 'arayacaksın'),
        ('ara-YAcAk?-Hz', 'arayacağız'),
        ('ara-YAcAk?-sHnHz', 'arayacaksınız'),
        ('git?-mA-Hm', 'gitmem'),
        ('üst-Hm', 'üstüm'),
        ("gitmiş-YDH-m", "gitmiştim")
    ]
    '''
    def run(self, test_result=None):
        return super(TestMorph, self).run(XTestResult())
    '''
    def setUp(self):
        self.processor = TurkishPostProcessor()

    def test_all(self):
        for sent,out in self.cases:

            sent = sent.replace("-","")
            with self.subTest(sent=sent,out=out):
                result = self.processor(sent)
                #print(sent,result,out)
                self.assertEqual(result,out)
                     
def main():
    # used for data generation
    morpher = TurkishPostProcessor()
    data = []

    words = [ "ev", "araba", "kitap?", "hak+", "tank", "yatak", "bur@un", "renk?", "rol^" ]
    suffixes = [ "-Hm", "-YHm", "-YdHm", "-YH", "-YlA", "-DA", "-NHn", "-ZHN", "-ZHN-YH", "-ZHN-YlA", "-ZHN-DA", "-ZHN-NHn" ]

    for word in words:
        for suffix in suffixes:
            nword = word + suffix
            data.append((nword, morpher(nword)))

    words = [ "gel", "git?", "oku", "öde" ]
    suffixes = [ "-DH-m", "-DH-n", "-DH-k", "-DH-nHz", "-Vyor-Hm", "-Vyor-sHn", "-Vyor-Hz", "-Vyor-sHnHz", "-YAcAk-Hm", "-YAcAk-sHn", "-YAcAk-Hz", "-YAcAk-sHnHz" ]

    for word in words:
        for suffix in suffixes:
            nword = word + suffix
            data.append((nword, morpher(nword)))
    for item in data:
        print(item,",",sep="")   

if __name__== '__main__':
    unittest.main()
    #main()