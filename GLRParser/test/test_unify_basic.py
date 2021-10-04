import sys, unittest, textwrap
sys.path.append("../..")
from GLRParser import Parser, UnifyError

class Param(dict):
    pass

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
        ({},{"pers":"*ppers"},{"pers":"3"}, {"ppers":"3"},{}),
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

    ### IMPORTANT Currently default copying types +- are ignored in Down Propagation
    # []<-(+,ppers=*pers)<-[pers=3,+neg]    up: [pers=3,+neg]  down: [ppers=3]
        ({},{"+":None,"ppers":"*pers"},{"pers":"3","neg":"+"}, {"pers":"3","neg":"+"},{"ppers":"3"}),
    # []<-(+,pers=*ppers)<-[pers=3,+neg]    up: [ppers=3,+neg]  down: [ppers=3]
        ({},{"+":None,"pers":"*ppers"},{"pers":"3","neg":"+"}, {"ppers":"3","neg":"+"},{}),
    # []<-(-,ppers=*pers,numb)<-[pers=3,+neg,numb=sing]    up: [pers=3,+neg]  down: [ppers=3]
        ({},{"-":None,"ppers":"*pers","numb":None},{"pers":"3","neg":"+","numb":"sing"}, {"pers":"3","neg":"+"},{"ppers":"3","numb":"sing"}),
    # []<-(-,pers=*ppers,numb)<-[pers=3,+neg,numb=sing]    up: [ppers=3,+neg]  down: [ppers=3]
        ({},{"-":None,"pers":"*ppers","numb":None},{"pers":"3","neg":"+","numb":"sing"}, {"neg":"+"},{"numb":"sing"}),

    ### IMPORTANT Currently ?! is ignored in Up Propagation
    # [?noplur]<- <-[+noplur]    up: [+noplur]  down: [+noplur]
        ({"noplur":"?"},None,{"noplur":"+"}, {"noplur":"+"},{"noplur":"+"}),
    # [?noplur]<- <-[]    up: []  down: X
        ({"noplur":"?"},None,{}, {},None),

    # [!noplur]<- <-[+noplur]    up: [+noplur]  down: X
        ({"noplur":"!"},None,{"noplur":"+"}, {"noplur":"+"},None),
    # [!noplur]<- <-[]    up: []  down: []
        ({"noplur":"!"},None,{}, {},{}),

    # [conn=?if]<- <-[conn=if]   up: [conn=if] down: [conn=if]
        ({"conn":"?if"},None,{"conn":"if"}, {"conn":"if"}, {"conn":"if"}),
    # [conn=?if]<- <-[conn=while]   up: [conn=while] down: X
        ({"conn":"?if"},None,{"conn":"while"}, {"conn":"while"},None),
    # [conn=?if]<- <-[]   up: [] down: X
        ({"conn":"?if"},None,{}, {},None),

    # [conn=!if]<- <-[conn=if]   up: [conn=if] down: X
        ({"conn":"!if"},None,{"conn":"if"}, {"conn":"if"}, None),
    # [conn=!if]<- <-[conn=while]   up: [conn=while] down: [conn=while]
        ({"conn":"!if"},None,{"conn":"while"}, {"conn":"while"},{"conn":"while"}),
    # [conn=!if]<- <-[]   up: [] down: None
        ({"conn":"!if"},None,{}, {},None),

    # [conn=~if]<- <-[conn=if]   up: X down: X
        ({"conn":"~if"},None,{"conn":"if"}, None, None),
    # [conn=~if]<- <-[conn=while]   up: [conn=while] down: [conn=while]
        ({"conn":"~if"},None,{"conn":"while"}, {"conn":"while"},{"conn":"while"}),
    # [conn=~if]<- <-[]   up: [conn=~if] down: [conn=~if]
        ({"conn":"~if"},None,{}, {"conn":"~if"},{"conn":"~if"}),
    # [conn=if]<- <-[conn=~if]   up: X down: X
        ({"conn":"if"},None,{"conn":"~if"}, None,None),
    # [conn=while]<- <-[conn=~if]   up: [conn=while] down: [conn=while]
        ({"conn":"while"},None,{"conn":"~if"}, {"conn":"while"},{"conn":"while"}),

    # [conn=~if]<- [conn=if] <-[]  up: [conn=~if] down: X
        ({"conn":"~if"},{"conn":"if"},{}, {"conn":"~if"}, None),
    # []<- [conn=if] <-[conn=~if]  up: X down: [conn=if]
        ({},{"conn":"if"},{"conn":"~if"}, None, {"conn":"if"}),
    # [conn=~if]<- [conn=while] <-[]  up: [conn=~if] down: [conn=while]
        ({"conn":"~if"},{"conn":"while"},{}, {"conn":"~if"}, {"conn":"while"}),
    # []<- [conn=while] <-[conn=~if]  up: [] down: [conn=while]
        ({}, {"conn":"while"},{"conn":"~if"}, {}, {"conn":"while"}),
    # [conn=if]<- [conn=~if] <-[]  up: X down: X
        ({"conn":"if"},{"conn":"~if"},{}, {"conn":"if"}, None),
    # []<- [conn=~if] <-[conn=if]  up: X down: [conn=~if]
        ({},{"conn":"~if"},{"conn":"if"}, None,{"conn":"~if"}),
    # [conn=while]<- [conn=~if] <-[]  up: [conn=while] down: [conn=while]
        ({"conn":"while"},{"conn":"~if"},{}, {"conn":"while"}, {"conn":"while"}),
    # []<- [conn=~if] <-[conn=while]  up: [] down: [conn=while]
        ({},{"conn":"~if"},{"conn":"while"}, {}, {"conn":"~if"}),

        ({"gap":"+"},{"gap":"-"},{"gap":"-"}, {"gap":"+"},None),
    ]

    def test_unify_basic(self):
        for dst,param,src,exp_up,exp_down in self.cases:

            with self.subTest(dst=dst,param=param,src=src):
               try:
                   checklist = {key:val for key,val in dst.items() if val[0] in '?!'}
                   _dst = {key:val for key,val in dst.items() if val[0] not in '?!'}
                   if param is not None:
                       param_type = [key for key,val in param.items() if key in '+-' ]
                       param = Param([(key,val) for key,val in param.items() if key not in '+-'])
                       param.param_type = param_type[0] if param_type else None
                   result = Parser.unify_up(_dst,param,src)
               except UnifyError:
                   result = None
               self.assertEqual(result, exp_up)

            with self.subTest(dst=dst,param=param,src=src):
               try:
                   checklist = {key:val for key,val in dst.items() if val[0] in '?!'}
                   _dst = {key:val for key,val in dst.items() if val[0] not in '?!'}
                   if param is not None:
                       param_type = [key for key,val in param.items() if key in '+-' ]
                       param = Param([(key,val) for key,val in param.items() if key not in '+-'])
                       param.param_type = param_type[0] if param_type else None
                   result = Parser.unify_down(_dst,param,src,checklist)
               except UnifyError:
                   result = None
               self.assertEqual(result, exp_down)


if __name__== '__main__':
    unittest.main()
