import logging
import socket
import sys

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

i = 0

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('0.0.0.0', 4242))
s.listen(1)
while True:
    c, a = s.accept()
    log.debug("Accepted connection from %r", a)
    c.sendall("Hello %r\n" % i)
    log.debug("Sent Hello %r" % i)
    c.shutdown(socket.SHUT_RDWR)
    c.close()
    log.debug("Closed connection")
    i += 1
