import logging
import sys

#loggingFormat = '%(asctime)s,%(msecs)03d %(levelname)-5.5s [%(processName)s-%(thread)d-%(threadName)s] [%(name)s] %(message)s (line %(lineno)d %(funcName)s)'
loggingFormat = '%(asctime)s,%(msecs)03d %(levelname)-5.5s [%(name)s] %(message)s (line %(lineno)d %(funcName)s)'
logging.basicConfig(level=logging.DEBUG, format=loggingFormat, datefmt='%Y-%m-%d %H:%M:%S')

log = logging.getLogger(__name__)
#log.setLevel(logging.DEBUG)
#ch = logging.StreamHandler(sys.stdout)
#ch.setLevel(logging.DEBUG)
## create formatter and add it to the handlers
##fmt = '%(asctime)s,%(msecs)03d %(levelname)-5.5s [%(processName)s-%(thread)d-%(threadName)s] [%(name)s] %(message)s (line %(lineno)d %(funcName)s)'
#fmt = '%(asctime)s,%(msecs)03d %(levelname)-5.5s [%(name)s] %(message)s (line %(lineno)d %(funcName)s)'
#formatter = logging.Formatter(fmt, datefmt='%Y-%m-%d %H:%M:%S')
#ch.setFormatter(formatter)
## add the handlers to the logger
#log.addHandler(ch)

from greenlet import greenlet, GreenletExit

def join(gr):
    ret = None
    while not gr.dead:
        ret = gr.switch()
        if isinstance(ret, GreenletExit):
            break
    return ret

#
#def test1():
#    print 12
#    gr2.switch()
#    print 34
#
#def test2():
#    print 56
#    gr1.switch()
#    print 78
#
#gr1 = greenlet(test1)
#gr2 = greenlet(test2)
#    
#join(gr1)
#join(gr2)
#
#
#def test1(x, y):
#    z = gr2.switch(x+y)
#    print z
#
#def test2(u):
#    print u
#    gr1.switch(42)
#
#gr1 = greenlet(test1)
#gr2 = greenlet(test2)
#gr1.switch("hello", " world")

import socket as pysocket

def recvall(s):
    data = []
    while True:
        n = s.recv(1024)
        if not n:
            log.debug("recvall done")
            break
        log.debug("recvall %r", n)
        data.append(n)
    s.shutdown(pysocket.SHUT_RDWR)
    s.close()
    return b''.join(data)

from jevent import ioloop
from jevent.socket import socket

gls = []
for i in xrange(2):
    s = socket()
    s.connect(("127.0.0.1", 4242))
    gl = greenlet(recvall)
    gls.append((i, s, gl))

for i in xrange(2):
    log.debug("%r %r", i, gls[i][2].switch(gls[i][1]))

for i in xrange(2):
    s = socket()
    s.connect(("127.0.0.1", 4242))
    gl = greenlet(recvall)
    log.debug("%r %r", i, gl.switch(s))

#for i, s, gl in gls:
#    log.debug("%r %r", i, gl.switch(s))

#import time
#s = pysocket.socket()
#s.connect(('127.0.0.1', 4242))
#s.setblocking(0)
#while True:
#    try:
#        print s.recv(1024)
#    except Exception, e:
#        import pdb; pdb.set_trace()
#        log.exception('')
#    time.sleep(1)

#d = "x" * 40960000
#import time
#s = pysocket.socket()
#s.connect(('127.0.0.1', 4242))
#s.setblocking(0)
#while True:
#    try:
#        print s.send(d)
#    except Exception, e:
#        log.exception('')
#        import pdb; pdb.set_trace()
#    time.sleep(1)
