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

def main_greenlets():
    from greenlet import greenlet, GreenletExit

    s = greenlet(run_server)
    c = greenlet(run_client)
    s.switch()
    log.info("Server started and switched back")
    c.switch()
    log.info("Client started and switched back")
    while not s.dead:
        if c.dead:
            log.info("Client dead, exiting")
            s.throw(GreenletExit())
            break
        c.switch()
        s.switch()

if __name__ == '__main__':
    loggingFormat = '%(asctime)s,%(msecs)03d %(levelname)-5.5s [%(name)s] %(message)s (line %(lineno)d %(funcName)s)'
    logging.basicConfig(level=logging.ERROR, format=loggingFormat, datefmt='%Y-%m-%d %H:%M:%S')
    
    main_greenlets()
