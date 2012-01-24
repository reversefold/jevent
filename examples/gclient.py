# Copyright: (c) 2012 Justin Patrin <papercrane@reversefold.com>

import greenlet
from greenlet import GreenletExit
import logging
import random
import sys
import socket as pysocket
import time

#from jevent import ioloop
#from jevent.socket import socket
from gevent.socket import socket

log = logging.getLogger(__name__)

def recvall(s, i):
    try:
    #    num = random.randint(0, 1) * 10240000
    #    num = (9 - i) * 102400
        num = 1023
    #    num = 1024 * 1024
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
    except:
        log.exception("recvall exception")
        pass

def main():
    while True:
        gls = []
        for i in xrange(1000):
            while True:
                try:
                    s = socket()
                except pysocket.error, e:
                    if e.errno != 24:
                        raise
                else:
                    break
            s.connect(("127.0.0.1", 2424))
                
            gl = greenlet.greenlet(recvall)
            gls.append((i, s, gl))
            gl.switch(s, i)
    
        while gls:
            for i, s, gl in gls:
                if gl.dead:
                    gls.remove((i, s, gl))
                else:
                    gl.switch()
        break

if __name__ == '__main__':
    loggingFormat = '%(asctime)s,%(msecs)03d %(levelname)-5.5s [%(name)s] %(message)s (line %(lineno)d %(funcName)s)'
    logging.basicConfig(level=logging.ERROR, format=loggingFormat, datefmt='%Y-%m-%d %H:%M:%S')
    
    main()
