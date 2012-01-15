import logging
import random
import sys
import time

#loggingFormat = '%(asctime)s,%(msecs)03d %(levelname)-5.5s [%(processName)s-%(thread)d-%(threadName)s] [%(name)s] %(message)s (line %(lineno)d %(funcName)s)'
loggingFormat = '%(asctime)s,%(msecs)03d %(levelname)-5.5s [%(name)s] %(message)s (line %(lineno)d %(funcName)s)'
logging.basicConfig(level=logging.DEBUG, format=loggingFormat, datefmt='%Y-%m-%d %H:%M:%S')

log = logging.getLogger(__name__)


import socket as pysocket
from greenlet import greenlet
from jevent import socket
#import socket

class connection(greenlet):
    def __init__(self, i, c, a):
        self.i = i
        self.c = c
        self.a = a

    def run(self):
        log.debug("Accepted connection from %r", self.a)
    #    c.recv(1)
    #    time.sleep(10)
    #    time.sleep(random.randint(0, 10))
        self.c.send("Hello %r\n" % self.i)
        log.debug("Sent Hello %r" % self.i)
        self.c.shutdown(pysocket.SHUT_RDWR)
        self.c.close()
        log.debug("Closed connection")

i = 0

s = socket.socket(pysocket.AF_INET, pysocket.SOCK_STREAM)
s.setsockopt(pysocket.SOL_SOCKET, pysocket.SO_REUSEADDR, 1)
s.bind(('0.0.0.0', 4242))
s.listen(10)
while True:
    c, a = s.accept()
    g = connection(i, c, a)
    g.switch()
    i += 1
