from greenlet import greenlet
import logging
import sys
import time as __time__
from jevent import time

log = logging.getLogger(__name__)

start = __time__.time()

def run_client():
    greenlet.getcurrent().parent.switch()
    for i in xrange(10):
        log.info("client: %s" % ((__time__.time() - start),))
        time.sleep(2)

def run_server():
    greenlet.getcurrent().parent.switch()
    for i in xrange(10):
        log.info("server: %s" % ((__time__.time() - start),))
        time.sleep(3)

def main_greenlets():

    s = greenlet(run_server)
    c = greenlet(run_client)
    s.switch()
    log.info("Server started and switched back")
    c.switch()
    log.info("Client started and switched back")
    while not c.dead:
        c.switch()
        s.switch()
    log.info("Client dead, exiting")
    from jevent import ioloop
    from examples import server
    ioloop._go = False
    server.go = False
    while not s.dead:
        try:
            s.switch()
        except:
            pass
    ioloop._go = True
    server.go = True

if __name__ == '__main__':
    #loggingFormat = '%(asctime)s,%(msecs)03d %(levelname)-5.5s [%(processName)s-%(thread)d-%(threadName)s] [%(name)s] %(message)s (line %(lineno)d %(funcName)s)'
    loggingFormat = '%(asctime)s,%(msecs)03d %(levelname)-5.5s [%(name)s] %(message)s (line %(lineno)d %(funcName)s)'
    logging.basicConfig(level=logging.INFO, format=loggingFormat, datefmt='%Y-%m-%d %H:%M:%S')
    
    main_greenlets()
