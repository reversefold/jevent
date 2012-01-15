from greenlet import greenlet
import logging
import socket as pysocket
from jevent import ioloop

log = logging.getLogger(__name__)

from proxy import Proxy

class socket(Proxy):
    def __init__(self, *args, **kwargs):
        log.debug("socket.__init__ %r %r", args, kwargs)
        if kwargs.get('socket', False):
            self.socket = kwargs['socket']
        else:
            self.socket = pysocket.socket(*args, **kwargs)
        super(socket, self).__init__(target=self.socket)

    def connect(self, *args, **kwargs):
        log.debug("socket.connect %r %r", args, kwargs)
        self.socket.connect(*args, **kwargs)
        self.socket.setblocking(0)

    def recv(self, *args, **kwargs):
        log.debug("socket.recv %r %r %r", self.socket.fileno(), args, kwargs)
        gl = greenlet(ioloop.coreloop.switch)
        return gl.switch(('recv', gl, self, args, kwargs))

    def send(self, *args, **kwargs):
        log.debug("socket.send %r %r %r", self.socket.fileno(), args, kwargs)
        gl = greenlet(ioloop.coreloop.switch)
        return gl.switch(('send', gl, self, args, kwargs))

    def accept(self, *args, **kwargs):
        log.debug("socket.accept %r %r %r", self.socket.fileno(), args, kwargs)
        self.socket.setblocking(0)
        gl = greenlet(ioloop.coreloop.switch)
        s, a = gl.switch(('accept', gl, self, args, kwargs))        
        return socket(socket=s), a 

    def close(self):
        log.debug("socket.close %r", self.socket.fileno())
        gl = greenlet(ioloop.coreloop.switch)
        gl.switch(('close', gl, self))
        self.socket.close()

    def shutdown(self, *args, **kwargs):
        try:
            self.socket.shutdown(*args, **kwargs)
        except pysocket.error, e:
            if not e.errno == 57:
                raise
            log.debug("Silencing error due to a FIN from the other side auto-shutting-down the socket")
