from greenlet import greenlet
import sys

def main():
#    def test1():
#        print 12
#        gr2.switch()
#        print 34
#    
#    def test2():
#        print 56
#        gr1.switch()
#        print 78
#    
#    gr1 = greenlet(test1)
#    gr2 = greenlet(test2)
#        
##    join(gr1)
##    join(gr2)
#    
#    def test1(x, y):
#        z = gr2.switch(x+y)
#        print z
#    
#    def test2(u):
#        print u
#        gr1.switch(42)
#    
#    gr1 = greenlet(test1)
#    gr2 = greenlet(test2)
#    gr1.switch("hello", " world")


    def test1():
        try:
            raise Exception("yo")
        except:
            print "test1 %r" % gr2.throw(*sys.exc_info())

    def test2():
        try:
            gr1.switch()
            print "ok"
        except:
            print sys.exc_info()

    gr1 = greenlet(test1)
    gr2 = greenlet(test2)
    gr2.switch()
    gr1.switch("hi")

if __name__ == '__main__':
     main()
