import logging
import random
import socket
import sys
import time

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
# create formatter and add it to the handlers
#fmt = '%(asctime)s,%(msecs)03d %(levelname)-5.5s [%(processName)s-%(thread)d-%(threadName)s] [%(name)s] %(message)s (line %(lineno)d %(funcName)s)'
fmt = '%(asctime)s,%(msecs)03d %(levelname)-5.5s [%(name)s] %(message)s (line %(lineno)d %(funcName)s)'
formatter = logging.Formatter(fmt, datefmt='%Y-%m-%d %H:%M:%S')
ch.setFormatter(formatter)
# add the handlers to the logger
log.addHandler(ch)

import ioloop
ioloop.log = log

from ioloop import socket
import socket as pysocket

i = 0

s = socket(pysocket.AF_INET, pysocket.SOCK_STREAM)
s.setsockopt(pysocket.SOL_SOCKET, pysocket.SO_REUSEADDR, 1)
s.bind(('0.0.0.0', 4242))
s.listen(10)
while True:
    c, a = s.accept()
    log.debug("Accepted connection from %r", a)
#    c.recv(1)
#    time.sleep(10)
    myi = i
    i += 1
#    time.sleep(random.randint(0, 10))
    c.send("Hello %r\n" % myi)
    log.debug("Sent Hello %r" % myi)
    c.shutdown(pysocket.SHUT_RDWR)
    c.close()
    log.debug("Closed connection")
