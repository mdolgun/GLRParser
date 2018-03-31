import sys, unittest, textwrap
sys.path.append("../..")
from GLRParser import Parser, UnifyError

class TestUnifyBasic(unittest.TestCase):
    cases = [ # dst,param,src,exp_up,exp_down(None if exception)
        ({},{"ng":"1"},{"det":"1"}, {}, {"ng":"1"}),
        ({"case":"acc"},{"ng":"1","det":None},{"det":"1"}, {"case":"acc","det":"1"}, {"case":"acc","det":"1","ng":"1"}),
        ({},{"ng":"1"},{"ng":"0"}, None, {"ng":"1"}),
        ({},None,{"det":"1"}, {"det":"1"}, {"det":"1"}),
        ({"det":"1","numb":"plur"},None,{"det":"1","pers":"1"}, {"det":"1","numb":"plur","pers":"1"}, {"det":"1","numb":"plur","pers":"1"}),
        ({"det":"0","numb":"plur"},None,{"det":"1","pers":"1"}, None, None),
        ({"det":"0","numb":"plur"},{"pers":None},{"det":"1","pers":"1"}, {"det":"0","numb":"plur","pers":"1"}, {"det":"0","numb":"plur","pers":"1"}),
        ({},{"ppers":"*pers"},{"pers":"3"}, {}, {"ppers":"3"}),
        ({"ppers":"1"},{"ppers":"*pers"},{"pers":"1"}, {"ppers":"1"}, {"ppers":"1"}),
        ({"ppers":"1"},{"ppers":"*pers"},{"pers":"3"}, {"ppers":"1"}, None),
        ({"ppers":"1"},{"pers":"*ppers"},{"pers":"3"}, None, {"ppers":"1"}),
        ({"ppers":"1"},{"ppers":"*pers"},{}, {"ppers":"1"}, {"ppers":"1"}),
        ({"noplur":"1"},None,{"noplur":"1"}, {"noplur":"1"},{"noplur":"1"}),
        ({"noplur":"1"},None,{"noplur":"1"}, {"noplur":"1"},{"noplur":"1"}),
        ({},None,{"noplur":"1"}, {"noplur":"1"},{"noplur":"1"}),
        ({"noplur":"1"},None,{}, {"noplur":"1"},{"noplur":"1"}),
        ({"noplur":"0"},None,{"noplur":"1"}, None,None),
        ({"noplur":"1"},None,{"noplur":"0"}, None,None),
        ({"noplur":"+"},None,{"noplur":"-"}, {"noplur":"+"},None),
        ({"noplur":"-"},None,{"noplur":"+"}, {"noplur":"+"},None),
        ({"noplur":"+"},None,{}, {"noplur":"+"},{"noplur":"+"}),
        ({},None,{"noplur":"+"}, {"noplur":"+"},{"noplur":"+"}),
        ({"noplur":"-"},None,{}, {"noplur":"-"},{"noplur":"-"}),
        ({},None,{"noplur":"-"}, {"noplur":"-"},{"noplur":"-"}),
        ({"noplur":"+"},None,{"noplur":"1"}, {"noplur":"1"},{"noplur":"1"}),
        ({"noplur":"1"},None,{"noplur":"+"}, {"noplur":"1"},{"noplur":"1"}),
        ({"noplur":"-"},None,{"noplur":"1"}, {"noplur":"1"},None),
        ({"noplur":"1"},None,{"noplur":"-"}, {"noplur":"1"},None),
    ]

    def test_unify_basic(self):
        for dst,param,src,exp_up,exp_down in self.cases:

            with self.subTest(dst=dst,param=param,src=src):
               try:
                   result = Parser.unify_up(dst,param,src)
               except UnifyError:
                   result = None
               self.assertEqual(result, exp_up)

            with self.subTest(dst=dst,param=param,src=src):
               try:
                   result = Parser.unify_down(dst,param,src)
               except UnifyError:
                   result = None
               self.assertEqual(result, exp_down)

 
if __name__== '__main__':
    unittest.main()
