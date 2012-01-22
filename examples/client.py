# Copyright: (c) 2012 Justin Patrin <papercrane@reversefold.com>

from greenlet import greenlet, GreenletExit
import logging
import random
import sys
import socket as pysocket
import time

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
    try:
        num = 1023
        log.debug("recvall %r %r", s, i)
        s.sendall("x" * num + "\n")
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
    except Exception, e:
#        log.exception("recvall exception")
        log.warn("recvall exception %r", e)
        pass

def main():
    while True:
        gls = []
        for i in xrange(1000):
            s = socket()
            s.connect(("127.0.0.1", 4242))
            gl = greenlet(recvall)
            gls.append((i, s, gl))
            gl.switch(s, i)
        
        while gls:
            for i, s, gl in gls:
                if gl.dead:
                    gls.remove((i, s, gl))
                else:
                    gl.switch()

if __name__ == '__main__':
    loggingFormat = '%(asctime)s,%(msecs)03d %(levelname)-5.5s [%(name)s] %(message)s (line %(lineno)d %(funcName)s)'
    logging.basicConfig(level=logging.ERROR, format=loggingFormat, datefmt='%Y-%m-%d %H:%M:%S')
    
    main()
