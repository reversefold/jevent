import logging
import sys
import time

log = logging.getLogger(__name__)


def run_client():
    from examples import gclient as client
    client.main()

def run_server():
    from examples import gserver as server
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

def main_threads():
    import threading

    s = threading.Thread(target=run_server)
    c = threading.Thread(target=run_client)
    s.start()
    log.info("Server started")
#    time.sleep(1)
    c.start()
    log.info("Client started")
    c.join()
    log.info("Client done")
#    import time
#    time.sleep(1)
#    log.info("Sleep done")
#    import ctypes
#    for tid, tobj in threading._active.items():
#        if tobj is s:
#            break
#    ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.pyobject(Exception))
    from examples import gserver as server
    from jevent import ioloop
    ioloop._go = False
    s.go = False
    s.join()
    log.info("Server done")

if __name__ == '__main__':
    #loggingFormat = '%(asctime)s,%(msecs)03d %(levelname)-5.5s [%(processName)s-%(thread)d-%(threadName)s] [%(name)s] %(message)s (line %(lineno)d %(funcName)s)'
    loggingFormat = '%(asctime)s,%(msecs)03d %(levelname)-5.5s [%(name)s] %(message)s (line %(lineno)d %(funcName)s)'
    logging.basicConfig(level=logging.ERROR, format=loggingFormat, datefmt='%Y-%m-%d %H:%M:%S')
    
#    main_greenlets()
    main_threads()
