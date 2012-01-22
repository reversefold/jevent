# Copyright: (c) 2012 Justin Patrin <papercrane@reversefold.com>

import logging
import random
import sys
import time

log = logging.getLogger(__name__)

import socket as pysocket
from greenlet import greenlet
from jevent import ioloop, socket

class connection(greenlet):
    def __init__(self, i, c, a):
        self.i = i
        self.c = c
        self.a = a

    def run(self):
        log.info("Accepted connection from %r", self.a)
        while True:
            d = self.c.recv(1024)
            if not d or d[-1] == "\n":
                break
        self.c.sendall("x" * 1010 + "Hello %r\n" % self.i)
        log.info("Sent Hello %r" % self.i)
        self.c.shutdown(pysocket.SHUT_RDWR)
        self.c.close()
        log.info("Closed connection")

go = True

def main():
    i = 0
    
    s = socket.socket(pysocket.AF_INET, pysocket.SOCK_STREAM)
    s.setsockopt(pysocket.SOL_SOCKET, pysocket.SO_REUSEADDR, 1)
    s.bind(('0.0.0.0', 4242))
    s.listen(5)
    while go:
        c, a = s.accept()
        g = connection(i, c, a)
        g.switch()
        i += 1
    s.shutdown(pysocket.SHUT_RDWR)
    s.close()
    log.info("Server stopped")

if __name__ == '__main__':
    loggingFormat = '%(asctime)s,%(msecs)03d %(levelname)-5.5s [%(name)s] %(message)s (line %(lineno)d %(funcName)s)'
    logging.basicConfig(level=logging.ERROR, format=loggingFormat, datefmt='%Y-%m-%d %H:%M:%S')
    
    main()
