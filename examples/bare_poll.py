from greenlet import greenlet
import logging
import socket
import select

log = logging.getLogger(__name__)

PORT=2424

MSG_LEN = 1024
g1 = None
g2 = None

def logit1():
    log.debug("logit1 start")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('0.0.0.0', PORT))
    s.listen(100)
    s.setblocking(0)
    
    p = select.poll()
    p.register(s.fileno(), select.POLLIN)
    j = 0
    while True:
        j += 1
        g2.switch()
        log.debug("logit1 poll")
        e = p.poll(10)
        if e and e[0][1] & select.POLLIN:
            c, a = s.accept()
            log.debug("Accepted connection from %r", a)
            c.setblocking(0)
            p2 = select.poll()

            p2.register(c.fileno(), select.POLLIN)
            l = MSG_LEN
            while l:
                log.debug("logit1 receive")
                e = p2.poll(1)
                if e and e[0][1] & select.POLLIN:
                    l -= len(c.recv(l))
                g2.switch()
            log.debug("logit1 unregister")
            p2.unregister(c.fileno())

            p2.register(c.fileno(), select.POLLOUT)
            log.debug("logit1 poll")
            msg = "x" * MSG_LEN
            while msg:
                log.debug("logit1 poll")
                e = p2.poll(1)
                if e and e[0][1] & select.POLLOUT:
                    msg = msg[c.send(msg):]
                g2.switch()
            log.debug("logit1 unregister")
            p2.unregister(c.fileno())

            try:
                c.shutdown(socket.SHUT_RDWR)
            except:
                pass
            c.close()
        else:
            log.debug("Nothing to poll")
        log.debug("logit1 poll")
        if not j % 100:
            log.info("j = %r", j)
    p.unregister(s.fileno())
    s.close()

def logit2():
    i = 0
    while True:
        i += 1
        g1.switch()
        log.debug("logit2 connect")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.setblocking(0)
        s.connect_ex(("127.0.0.1", PORT))
        p = select.poll()

        p.register(s.fileno(), select.POLLOUT)
        log.debug("logit2 poll")
        msg = "x" * MSG_LEN
        while msg:
            log.debug("logit2 poll")
            e = p.poll(1)
            if e and e[0][1] & select.POLLOUT:
                msg = msg[s.send(msg):]
            g1.switch()
        log.debug("logit2 unregister")
        p.unregister(s.fileno())

        p.register(s.fileno(), select.POLLIN)
        l = MSG_LEN
        while l:
            log.debug("logit2 receive")
            e = p.poll(1)
            if e and e[0][1] & select.POLLIN:
                l -= len(s.recv(l))
            g1.switch()
        log.debug("logit2 unregister")
        p.unregister(s.fileno())

        try:
            s.shutdown(socket.SHUT_RDWR)
        except:
            pass
        s.close()
        if not i % 100:
            log.info("i = %r", i)

def main():
    loggingFormat = '%(asctime)s,%(msecs)03d %(levelname)-5.5s [%(name)s] %(message)s (line %(lineno)d %(funcName)s)'
    logging.basicConfig(level=logging.INFO, format=loggingFormat, datefmt='%Y-%m-%d %H:%M:%S')

    global g1, g2
    g1 = greenlet(logit1)
    g2 = greenlet(logit2)
    
    g1.switch()

if __name__ == '__main__':
    main()
