import logging
import sys
import time

log = logging.getLogger(__name__)


def run_client():
    from examples import client
    client.main()

def run_server():
    from examples import server
    server.main()

def maing():
    from greenlet import greenlet

    s = greenlet(run_server)
    c = greenlet(run_client)
    s.switch()
    log.info("Server started and switched back")
    c.switch()
    log.info("Client started and switched back")
    while not s.dead:
        if c.dead:
            sys.exit(0)
        c.switch()
        s.switch()

def maint():
    from threading import Thread

    s = Thread(target=run_server)
    c = Thread(target=run_client)
    s.start()
    log.info("Server started")
    c.start()
    log.info("Client started")
    c.join()
    log.info("Client done")
    s.join()
    log.info("Server done")

if __name__ == '__main__':
    #loggingFormat = '%(asctime)s,%(msecs)03d %(levelname)-5.5s [%(processName)s-%(thread)d-%(threadName)s] [%(name)s] %(message)s (line %(lineno)d %(funcName)s)'
    loggingFormat = '%(asctime)s,%(msecs)03d %(levelname)-5.5s [%(name)s] %(message)s (line %(lineno)d %(funcName)s)'
    logging.basicConfig(level=logging.DEBUG, format=loggingFormat, datefmt='%Y-%m-%d %H:%M:%S')
    
#    maing()
    maint()
