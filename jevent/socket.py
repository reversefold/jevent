import greenlet
import logging
import select
__socket__ = __import__('socket')
from jevent import ioloop

log = logging.getLogger(__name__)

from proxy import Proxy

def lim(s, l=50):
    ss = str(s)
    return s if len(ss) < l else (ss[:l] + '...')

class socket(Proxy):
    def __init__(self, *args, **kwargs):
        log.debug("socket.__init__ %r %r", args, kwargs)
        if kwargs.get('socket', False):
            self.socket = kwargs['socket']
        else:
            self.socket = __socket__.socket(*args, **kwargs)
        super(socket, self).__init__(target=self.socket)

    def _check_fileno(self):
        if self.fileno() == -1:
            log.error("fileno is -1")
            import pdb;pdb.set_trace()

    def connect(self, *args, **kwargs):
        log.debug("socket.connect %r %r", args, kwargs)
        #self._check_fileno()
        self.socket.connect(*args, **kwargs)
        self.socket.setblocking(0)
        # TODO: no async here?

    def _do_operation(self, operation, flag, args, kwargs):
        #self._check_fileno()
#        if ioloop.IDLE:
#            ioloop.coreloop.switch()
        try:
            ret = getattr(self.socket, operation)(*args, **kwargs)

        except __socket__.error, e:
            if e.errno != 35: #Resource temporarily unavailable
                raise
            log.debug("Asynchronous socket is not ready for %r %r %r", operation, self, e)
            ioloop.coreloop.register(
                { 'greenlet': greenlet.getcurrent(),
                  'socket': self,
                  'args': args,
                  'kwargs': kwargs },
                flag,
                operation)

            try:
                ## TODO: don't really like this
                while True:
                #    try:
                #        ret = getattr(self.socket, operation)(*args, **kwargs)
                #    except __socket__.error, e:
                #        if e.errno != 35: #Resource temporarily unavailable
                #            raise
                #        log.debug("Asynchronous socket is not ready for %r %r %r", operation, self, e)
                    ret = ioloop.coreloop.switch()
                    if ioloop.IDLE and ret is ioloop.noop:
                        log.debug("noop")
                        continue
                    break
            finally:
                ioloop.coreloop.unregister(self.fileno(), flag, operation)

        log.debug(" return %r %r", lim(ret), self)
        return ret

    def recv(self, *args, **kwargs):
        log.debug("socket.recv %r %r %r", self.socket.fileno(), lim(args), lim(kwargs))
        return self._do_operation('recv', select.POLLIN, args, kwargs)

    def send(self, *args, **kwargs):
        log.debug("socket.send %r %r %r", self.socket.fileno(), lim(args), lim(kwargs))
        return self._do_operation('send', select.POLLOUT, args, kwargs)

    def accept(self, *args, **kwargs):
        log.debug("socket.accept %r %r %r", self.socket.fileno(), args, kwargs)
        self.socket.setblocking(0)
        s, a = self._do_operation('accept', select.POLLIN, args, kwargs)
        return socket(socket=s), a 

    def sendall(self, data):
        # TODO: use self.socket.sendall?
        log.debug("Sending %r bytes", len(data))
        while data:
            data = data[self.send(data):]
            log.debug("%r remaining", len(data))
            #time.sleep(0.1)

#    def close(self):
#        log.debug("socket.close %r", self.socket.fileno())
#        #self._check_fileno()
#        ioloop.coreloop.unregister(self.fileno(), force=True)
#        self.socket.close()

    def shutdown(self, *args, **kwargs):
        log.debug("socket.shutdown %r", self.socket.fileno())
        #self._check_fileno()
        try:
            self.socket.shutdown(*args, **kwargs)
        except __socket__.error, e:
            if not e.errno == 57:
                raise
            log.debug("Silencing error due to a FIN from the other side auto-shutting-down the socket")

    def setblocking(self, *args, **kwargs):
        raise Exception("This is a non-blocking implementation of a blocking socket, you can't setblocking on me")
