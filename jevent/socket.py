import greenlet
import logging
__socket__ = __import__('socket')
from jevent import ioloop

log = logging.getLogger(__name__)

from proxy import Proxy

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

    def recv(self, *args, **kwargs):
        log.debug("socket.recv %r %r %r", self.socket.fileno(), args, kwargs)
        #self._check_fileno()
        return ioloop.coreloop.switch(('recv', greenlet.getcurrent(), self, args, kwargs))

    def send(self, *args, **kwargs):
        log.debug("socket.send %r %r %r", self.socket.fileno(), args, kwargs)
        #self._check_fileno()
        return ioloop.coreloop.switch(('send', greenlet.getcurrent(), self, args, kwargs))

    def accept(self, *args, **kwargs):
        log.debug("socket.accept %r %r %r", self.socket.fileno(), args, kwargs)
        #self._check_fileno()
        self.socket.setblocking(0)
        s, a = ioloop.coreloop.switch(('accept', greenlet.getcurrent(), self, args, kwargs))        
        return socket(socket=s), a 

    def close(self):
        log.debug("socket.close %r", self.socket.fileno())
        #self._check_fileno()
        ioloop.coreloop.switch(('close', greenlet.getcurrent(), self))
        self.socket.close()

    def shutdown(self, *args, **kwargs):
        log.debug("socket.fileno %r", self.socket.fileno())
        #self._check_fileno()
        try:
            self.socket.shutdown(*args, **kwargs)
        except __socket__.error, e:
            if not e.errno == 57:
                raise
            log.debug("Silencing error due to a FIN from the other side auto-shutting-down the socket")

    def setblocking(self, *args, **kwargs):
        raise Exception("This is a non-blocking implementation of a blocking socket, you can't setblocking on me")
