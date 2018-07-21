import sys, unittest, textwrap
sys.path.append("../..")
from GLRParser import Parser, UnifyError


class TestUnifyBasic(unittest.TestCase):
    cases = [ # dst,param,src,exp_up,exp_down(None if exception)
    # []<-(ng=1)<-[det=1]    up: []  down: [ng=1]
        ({},{"ng":"1"},{"det":"1"}, {}, {"ng":"1"}), 
    # [case=acc]<-(ng=1,det)<-[det=1]    up: [case=acc,det=1]  down: [case=acc,det=1,ng=1]
        ({"case":"acc"},{"ng":"1","det":None},{"det":"1"}, {"case":"acc","det":"1"}, {"case":"acc","det":"1","ng":"1"}),
    # []<-(ng=1)<-[ng=0]    up: X  down: [ng=1]
        ({},{"ng":"1"},{"ng":"0"}, None, {"ng":"1"}),
    # []<- <-[det=1]    up: [det=1]  down: [det=1]
        ({},None,{"det":"1"}, {"det":"1"}, {"det":"1"}),
    # [det=1,numb=plur]<- <-[det=1,pers=1]    up: [det=1,numb=plur,pers=1]  down: [det=1,numb=plur,pers=1]
        ({"det":"1","numb":"plur"},None,{"det":"1","pers":"1"}, {"det":"1","numb":"plur","pers":"1"}, {"det":"1","numb":"plur","pers":"1"}),
    # [det=0,numb=plur]<- <-[det=1,pers=1]    up: X  down: X
        ({"det":"0","numb":"plur"},None,{"det":"1","pers":"1"}, None, None),
    # [det=0,numb=plur]<-(pers)<-[det=1,pers=1]    up: [det=0,numb=plur,pers=1]  down: [det=0,numb=plur,pers=1]
        ({"det":"0","numb":"plur"},{"pers":None},{"det":"1","pers":"1"}, {"det":"0","numb":"plur","pers":"1"}, {"det":"0","numb":"plur","pers":"1"}),
    # []<-(ppers=*pers)<-[pers=3]    up: []  down: [ppers=3]
        ({},{"ppers":"*pers"},{"pers":"3"}, {}, {"ppers":"3"}),
    # []<-(pers=*ppers)<-[pers=3]    up: [ppers=3]  down: []
        ({},{"ppers":"*pers"},{"pers":"3"}, {}, {"ppers":"3"}),
    # [ppers=1]<-(ppers=*pers)<-[pers=1]    up: [ppers=1]  down: [ppers=1]
        ({"ppers":"1"},{"ppers":"*pers"},{"pers":"1"}, {"ppers":"1"}, {"ppers":"1"}),
    # [ppers=1]<-(ppers=*pers)<-[pers=3]    up: [ppers=1]  down: X
        ({"ppers":"1"},{"ppers":"*pers"},{"pers":"3"}, {"ppers":"1"}, None),
    # [ppers=1]<-(pers=*ppers)<-[pers=3]    up: X  down: [ppers=1]
        ({"ppers":"1"},{"pers":"*ppers"},{"pers":"3"}, None, {"ppers":"1"}),
    # [ppers=1]<-(ppers=*pers)<-[]    up: [ppers=1]  down: [ppers=1]
        ({"ppers":"1"},{"ppers":"*pers"},{}, {"ppers":"1"}, {"ppers":"1"}),

        ({"noplur":"1"},None,{"noplur":"1"}, {"noplur":"1"},{"noplur":"1"}),
        ({"noplur":"1"},None,{"noplur":"1"}, {"noplur":"1"},{"noplur":"1"}),
        ({},None,{"noplur":"1"}, {"noplur":"1"},{"noplur":"1"}),
        ({"noplur":"1"},None,{}, {"noplur":"1"},{"noplur":"1"}),
        ({"noplur":"0"},None,{"noplur":"1"}, None,None),
        ({"noplur":"1"},None,{"noplur":"0"}, None,None),

    # [?noplur]<- <-[+noplur]    up: [+noplur]  down: [+noplur]
        ({"noplur":"?"},None,{"noplur":"+"}, {"noplur":"+"}, {"noplur":"+"}),
    # [?noplur]<- <-[]    up: []  down: None
        #({"noplur":"?"},None,{}, {"noplur":"?"},None), !OLD method works this way!
        ({"noplur":"?"},None,{}, {},None),
    # [?noplur]<- <-[!noplur]    up: None  down: None
        ({"noplur":"?"},None,{"noplur":"!"}, None,None),

        ({"noplur":"+"},None,{"noplur":"!"}, None, None),
        ({"noplur":"!"},None,{"noplur":"+"}, None, None),
        ({},None,{"noplur":"!"}, {"noplur":"!"},{"noplur":"!"}),
        ({"noplur":"!"},None,{}, {"noplur":"!"},{"noplur":"!"}),

    # []<- <-[@numb=plur,@pers=3]    up: [] down: []
        ({},None,{"@numb":"plur","@pers":"3"}, {},{}),
    # []<-(@numb)<-[@numb=plur,@pers=3]    up: [] down: [numb=plur] 
        ({},{"@numb":None},{"@numb":"plur","@pers":"3"}, {},{"numb":"plur"}),
    # []<-(@numb)<-[numb=plur,pers=3]    up: [@numb=plur] down: [] 
        ({},{"@numb":None},{"numb":"plur","pers":"3"}, {"@numb":"plur"},{}),
    # []<-(@*)<-[@numb=plur,@pers=3]    up: [] down: [numb=plur,pers=3] 
        ({},{"@*":None},{"@numb":"plur","@pers":"3"}, {},{"numb":"plur","pers":"3"}),
    # []<-(@*)<-[numb=plur,pers=3]    up: [@numb=plur,@pers=3] down: [] 
        ({},{"@*":None},{"numb":"plur","pers":"3"}, {"@numb":"plur","@pers":"3"},{}),
    ]

    def test_unify_basic(self):
        for dst,param,src,exp_up,exp_down in self.cases:

            with self.subTest(dst=dst,param=param,src=src):
               try:
                   checklist = [key for key,val in dst.items() if val=='?']
                   _dst = {key:val for key,val in dst.items() if val!='?'}
                   result = Parser.unify_up(_dst,param,src,checklist)
               except UnifyError:
                   result = None
               self.assertEqual(result, exp_up)

            with self.subTest(dst=dst,param=param,src=src):
               try:
                   checklist = [key for key,val in dst.items() if val=='?']
                   _dst = {key:val for key,val in dst.items() if val!='?'}
                   result = Parser.unify_down(_dst,param,src,checklist)
               except UnifyError:
                   result = None
               self.assertEqual(result, exp_down)


if __name__== '__main__':
    unittest.main()
