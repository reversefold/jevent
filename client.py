from greenlet import greenlet, GreenletExit
import logging
import random
import sys
import socket as pysocket

from jevent import ioloop
from jevent.socket import socket

log = logging.getLogger(__name__)

def join(gr):
    ret = None
    while not gr.dead:
        ret = gr.switch()
        if isinstance(ret, GreenletExit):
            break
    return ret

def recvall(s, i):
#    num = random.randint(0, 1) * 10240000
    num = (9 - i) * 1024000
#    num = 1
    sendall(s, "x" * num + "\n")
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
    log.info("%r %r", i, b''.join(data))

def sendall(s, data):
    log.info("Sending %r bytes", len(data))
    while data:
        data = data[s.send(data):]

def main():
    #loggingFormat = '%(asctime)s,%(msecs)03d %(levelname)-5.5s [%(processName)s-%(thread)d-%(threadName)s] [%(name)s] %(message)s (line %(lineno)d %(funcName)s)'
    loggingFormat = '%(asctime)s,%(msecs)03d %(levelname)-5.5s [%(name)s] %(message)s (line %(lineno)d %(funcName)s)'
    logging.basicConfig(level=logging.INFO, format=loggingFormat, datefmt='%Y-%m-%d %H:%M:%S')
    
    gls = []
    for i in xrange(10):
        s = socket()
        s.connect(("127.0.0.1", 4242))
        gl = greenlet(recvall)
        gls.append((i, s, gl))
        gl.switch(s, i)
    
#    for i in xrange(10):
#        log.info("%r %r", i, gls[i][2].switch(gls[i][1], i))
    
#    while gls:
#        for i, s, gl in gls:
#            if gl.dead:
#                gls.remove((i, s, gl))
#            ioloop.coreloop.switch()
#
#    for i in xrange(4):
#        s = socket()
#        s.connect(("127.0.0.1", 4242))
#        gl = greenlet(recvall)
#        gls.append((i, s, gl))
#        log.info("%r %r", i, gl.switch(s, i))

    while gls:
        for i, s, gl in gls:
            if gl.dead:
                gls.remove((i, s, gl))
            ioloop.coreloop.switch()
    
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

if __name__ == '__main__':
     main()
