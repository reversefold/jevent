import logging
import random
import sys
import time

log = logging.getLogger(__name__)


import socket as pysocket
from greenlet import greenlet
from jevent import ioloop, socket
#import socket

class connection(greenlet):
    def __init__(self, i, c, a):
        self.i = i
        self.c = c
        self.a = a

    def run(self):
        log.info("Accepted connection from %r", self.a)
#        self.c.setblocking(0)
#        try:
#            self.c.recv(1024)
#        except:
#            log.error(sys.exc_info())
#        self.c.setblocking(1)
    #    c.recv(1)
    #    time.sleep(10)
    #    time.sleep(random.randint(0, 10))
        while True:
            d = self.c.recv(1024)
            if not d or d[-1] == "\n":
                break
            #time.sleep(0.1)
        self.c.sendall("Hello %r\n" % self.i)
        log.info("Sent Hello %r" % self.i)
        self.c.shutdown(pysocket.SHUT_RDWR)
        self.c.close()
        log.info("Closed connection")

def main():
    #loggingFormat = '%(asctime)s,%(msecs)03d %(levelname)-5.5s [%(processName)s-%(thread)d-%(threadName)s] [%(name)s] %(message)s (line %(lineno)d %(funcName)s)'
    loggingFormat = '%(asctime)s,%(msecs)03d %(levelname)-5.5s [%(name)s] %(message)s (line %(lineno)d %(funcName)s)'
    logging.basicConfig(level=logging.INFO, format=loggingFormat, datefmt='%Y-%m-%d %H:%M:%S')
    
    i = 0
    
    s = socket.socket(pysocket.AF_INET, pysocket.SOCK_STREAM)
    s.setsockopt(pysocket.SOL_SOCKET, pysocket.SO_REUSEADDR, 1)
    s.bind(('0.0.0.0', 4242))
    s.listen(5)
    while True:
        if ioloop.IDLE:
            ioloop.coreloop.switch()
        log.info("accept()")
        c, a = s.accept()
        g = connection(i, c, a)
        g.switch()
    #    g.run()
        i += 1

if __name__ == '__main__':
     main()
