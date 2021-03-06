# Copyright: (c) 2012 Justin Patrin <papercrane@reversefold.com>

import errno
import greenlet
import inspect
import logging
import select
__socket__ = __import__('socket')
from jevent import ioloop

log = logging.getLogger(__name__)

from errno import EINVAL, EWOULDBLOCK, EINPROGRESS, EALREADY, EAGAIN, EISCONN

from proxy import Proxy

def lim(s, l=50):
    ss = str(s)
    return s if len(ss) < l else (ss[:l / 2] + '...' + ss[-l / 2:])

class socket(Proxy):
    def __init__(self, *args, **kwargs):
        log.debug("socket.__init__ %r %r", args, kwargs)
        if kwargs.get('socket', False):
            self.socket = kwargs['socket']
        else:
            self.socket = __socket__.socket(*args, **kwargs)
        self._blocking = 1
        super(socket, self).__init__(target=self.socket)
        self.socket.setblocking(0)

    def connect(self, *args, **kwargs):
        log.debug("socket.connect %r %r", args, kwargs)
        return self._do_operation('connect', select.POLLOUT, self.socket.connect, args, kwargs)

    def _do_operation(self, operation, flag, func, args, kwargs):
        # loop until we get a response from the operation
        while ioloop._go:
            try:
                ret = func(*args, **kwargs)
                break

            except __socket__.error, e:
                if operation == 'connect' and e.errno == errno.EISCONN: # transport endpoint is connected
                    return
                if (e.errno != errno.EWOULDBLOCK #Resource temporarily unavailable
                    and e.errno != errno.EINPROGRESS #Operation now in progress
                    and e.errno != errno.EALREADY
#                    and e.errno != errno.EMFILE #Too many open files
                ): #Too many open files
                    raise
                log.debug("Asynchronous socket is not ready for %r %r %r", operation, self, e)
                ioloop.coreloop().register(self.fileno(), flag)
    
                try:
                    # loop until we don't get a noop (which means we should be ready for our operation)
                    while True:
                        ret = ioloop.coreloop().switch()
                        if ioloop.IDLE and ret is ioloop.noop:
                            log.debug("noop")
                            continue
                        break
                finally:
                    ioloop.coreloop().unregister(self.fileno(), flag)
                if operation == 'connect':# and e.errno != errno.EMFILE:
                    # We don't want to retry connecting, so just return now
                    return

        log.debug(" return %r %r", lim(ret), self)
        return ret

    def recv(self, *args, **kwargs):
        log.debug("socket.recv %r %r %r", self.socket.fileno(), lim(args), lim(kwargs))
        return self._do_operation('recv', select.POLLIN, self.socket.recv, args, kwargs)

    def send(self, *args, **kwargs):
        log.debug("socket.send %r %r %r", self.socket.fileno(), lim(args), lim(kwargs))
        return self._do_operation('send', select.POLLOUT, self.socket.send, args, kwargs)

    def accept(self, *args, **kwargs):
        log.debug("socket.accept %r %r %r", self.socket.fileno(), args, kwargs)
        ret = self._do_operation('accept', select.POLLIN, self.socket.accept, args, kwargs)
        try:
            s, a = ret
        except TypeError, e:
            raise __socket__.error("Accept failed")
        return socket(socket=s), a 

    def sendall(self, data):
        # TODO: use self.socket.sendall?
        log.debug("Sending %r bytes", len(data))
        while data:
            data = data[self.send(data):]
            log.debug("%r remaining", len(data))

    def shutdown(self, *args, **kwargs):
        log.debug("socket.shutdown %r", self.socket.fileno())
        try:
            self.socket.shutdown(*args, **kwargs)
        except __socket__.error, e:
            if not e.errno == errno.ENOTCONN: # Not connected
                raise
            log.debug("Silencing error due to a FIN from the other side auto-shutting-down the socket")

    def setblocking(self, block):
        if self._blocking == block:
            return
        self._blocking = block
        for name, method in inspect.getmembers(self, inspect.ismethod):
            if name == 'setblocking' or name.startswith('_'):
                continue
            if self._blocking:
                setattr(self, name, getattr(self, '_orig_' + name))
            else:
                setattr(self, '_orig_' + name, getattr(self, name))
                setattr(self, name, getattr(self.socket, name))
