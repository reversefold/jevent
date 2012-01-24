# Copyright: (c) 2012 Justin Patrin <papercrane@reversefold.com>

import logging
import random
import sys
import time

log = logging.getLogger(__name__)

import socket as pysocket
from greenlet import greenlet
from gevent import socket

i = 0

def handle(c, a):
    global i
    i += 1
    log.info("Accepted connection from %r", a)
    while True:
        d = c.recv(1024)
        if not d or d[-1] == "\n":
            break
    c.sendall("x" * 1010 + "Hello %r\n" % i)
    log.info("Sent Hello %r" % i)
    c.shutdown(pysocket.SHUT_RDWR)
    c.close()
    log.info("Closed connection")

go = True

def main():
    from gevent.server import StreamServer
    from gevent.pool import Pool as Group
    
    port = 2424
    server = StreamServer(('0.0.0.0', port), handle, spawn=Group())
    server.serve_forever()

#    s = socket.socket(pysocket.AF_INET, pysocket.SOCK_STREAM)
#    s.setsockopt(pysocket.SOL_SOCKET, pysocket.SO_REUSEADDR, 1)
#    s.bind(('0.0.0.0', 4242))
#    s.listen(5)
#    while go:
#        c, a = s.accept()
#        g = connection(i, c, a)
#        g.switch()
#        i += 1
#    s.shutdown(pysocket.SHUT_RDWR)
#    s.close()
    log.info("Server stopped")

if __name__ == '__main__':
    loggingFormat = '%(asctime)s,%(msecs)03d %(levelname)-5.5s [%(name)s] %(message)s (line %(lineno)d %(funcName)s)'
    logging.basicConfig(level=logging.ERROR, format=loggingFormat, datefmt='%Y-%m-%d %H:%M:%S')
    
    main()
