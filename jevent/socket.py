from greenlet import greenlet
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
        self.greenlet = greenlet(self._run)
        self.greenlet.switch()

    def connect(self, *args, **kwargs):
        log.debug("socket.connect %r %r", args, kwargs)
        self.socket.connect(*args, **kwargs)
        self.socket.setblocking(0)
        # TODO: no async here?

    def recv(self, *args, **kwargs):
        log.debug("socket.recv %r %r %r", self.socket.fileno(), args, kwargs)
        return self.greenlet.switch(('recv', self.greenlet, self, args, kwargs))

    def send(self, *args, **kwargs):
        log.debug("socket.send %r %r %r", self.socket.fileno(), args, kwargs)
        return self.greenlet.switch(('send', self.greenlet, self, args, kwargs))

    def accept(self, *args, **kwargs):
        log.debug("socket.accept %r %r %r", self.socket.fileno(), args, kwargs)
        self.socket.setblocking(0)
        s, a = self.greenlet.switch(('accept', self.greenlet, self, args, kwargs))        
        return socket(socket=s), a 

    def close(self):
        log.debug("socket.close %r", self.socket.fileno())
        self.greenlet.switch(('close', self.greenlet, self))
        self.socket.close()

    def shutdown(self, *args, **kwargs):
        try:
            self.socket.shutdown(*args, **kwargs)
        except __socket__.error, e:
            if not e.errno == 57:
                raise
            log.debug("Silencing error due to a FIN from the other side auto-shutting-down the socket")

    def setblocking(self, *args, **kwargs):
        raise Exception("This is a non-blocking implementation of a blocking socket, you can't setblocking on me")

    
    def _run(self):
        # switch back to the parent at first (i.e. right back to our __init__)
        r = self.greenlet.parent.switch()
        while True:
            ret = ioloop.coreloop.switch(r)
            r = self.greenlet.parent.switch(ret)
