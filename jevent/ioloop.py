import logging
from greenlet import greenlet
import select
pysocket = __import__('socket')

from jevent import JEventException

log = logging.getLogger(__name__)

class ioloop(greenlet):
    def __init__(self):
        log.debug("ioloop.__init__")
        super(ioloop, self).__init__()

        self.registered = {}
        self.poll = select.poll()

    def register(self, record, flag, operation):
        fileno = record['socket'].fileno()
        log.debug("ioloop.register %r %r", fileno, flag)
#        if fileno == -1:
#            log.error("fileno is -1")
#            import pdb;pdb.set_trace()

        if fileno in self.registered:
            if operation in self.registered[fileno]['operations']:
                raise JEventException("%r already registered for operation %r" % (fileno, flag))

            self.registered[fileno]['flags'] |= flag
            self.registered[fileno]['operations'][operation] = record
            self.poll.modify(fileno, self.registered[fileno]['flags'])

        else:
            self.registered[fileno] = {
                'operations': { operation: record },
                'flags': flag
                }
            self.poll.register(fileno, flag)

    def unregister(self, fileno, flag=None, operation=None, force=False):
        log.debug("ioloop.unregister %r %r", fileno, flag)
        if fileno not in self.registered:
            log.debug("fileno not registered previously %r %r", fileno, flag)
            return
        
        r = self.registered[fileno]['flags']
        if force:
            r = 0
        else:
            r &= ~flag

        if r:
            log.debug("fileno unregistered flag %r %r %r", fileno, flag, r)
            self.poll.modify(fileno, r)
            self.registered[fileno]['flags'] = r
            del self.registered[fileno]['operations'][operation]

        else:
            log.debug("fileno fully unregistered %r", fileno)
            self.poll.unregister(fileno)
            del self.registered[fileno]

    def socket_recv(self, gl, socket, args, kwargs):
        log.debug("ioloop.socket_recv %r %r %r %r %r", gl, socket, socket.fileno(), args, kwargs)
        r = { 'greenlet': gl,
              'socket': socket,
              'args': args,
              'kwargs': kwargs }
        if not self.do_recv(r):
            self.register(r, select.POLLIN, 'recv')

    def do_recv(self, r):
        log.debug("do_recv %r", r)
        try:
            data = r['socket'].socket.recv(*r['args'], **r['kwargs'])

        except pysocket.error, e:
            if e.errno == 35: #Resource temporarily unavailable
                log.debug("Asynchronous socket has no readable data %r %r", r, e)
            else:
                self.handle_switch(r['greenlet'].throw(*sys.exc_info()))

        except:
            self.handle_switch(r['greenlet'].throw(*sys.exc_info()))             

        else:
            log.debug(" data %r %r", r, data)
            self.unregister(r['socket'].fileno(), select.POLLIN, 'recv')
            log.info("recv, Switching to %r with %r", r, data)
            self.handle_switch(r['greenlet'].switch(data))
            return True

        return False

    def socket_send(self, gl, socket, args, kwargs):
        log.debug("ioloop.socket_send %r %r %r %r %r", gl, socket, socket.fileno(), args, kwargs)
        r = { 'greenlet': gl,
              'socket': socket,
              'args': args,
              'kwargs': kwargs}
        if not self.do_send(r):
            self.register(r, select.POLLOUT, 'send')

    def do_send(self, r):
        log.debug("do_send %r", r)
        try:
            ret = r['socket'].socket.send(*r['args'], **r['kwargs'])

        except pysocket.error, e:
            if e.errno == 35: #Resource temporarily unavailable
                log.debug("Asynchronous socket is not ready to send data %r %r", r, e)
            else:
                self.handle_switch(r['greenlet'].throw(*sys.exc_info()))

        except:
            self.handle_switch(r['greenlet'].throw(*sys.exc_info()))             

        else:
            log.debug(" return %r %r", ret, r)
            log.info("send, Switching to %r with %r", r, ret)
            self.unregister(r['socket'].fileno(), select.POLLOUT, 'send')
            self.handle_switch(r['greenlet'].switch(ret))
            return True

        return False

    def socket_accept(self, gl, socket, args, kwargs):
        log.debug("ioloop.accept %r %r %r %r %r", gl, socket, socket.fileno(), args, kwargs)
        r = { 'greenlet': gl,
              'socket': socket,
              'args': args,
              'kwargs': kwargs}
        if not self.do_accept(r):
            self.register(r, select.POLLIN, 'accept')

    def do_accept(self, r):
        log.debug("do_accept %r", r)
        try:
             data = r['socket'].socket.accept(*r['args'], **r['kwargs'])

        except pysocket.error, e:
            if e.errno == 35: #Resource temporarily unavailable
                log.debug("Asynchronous socket is not ready to accept %r %r", r, e)
            else:
                self.handle_switch(r['greenlet'].throw(*sys.exc_info()))

        except:
             self.handle_switch(r['greenlet'].throw(*sys.exc_info()))

        else:
            log.debug(" data %r %r", data, r)
            self.unregister(r['socket'].fileno(), select.POLLIN, 'accept')
            log.info("accept, Switching to %r with %r", r, data)
            self.handle_switch(r['greenlet'].switch(data))
            return True

        return False

    def socket_close(self, gl, socket):
        log.debug("ioloop.socket_close %r %r %r", gl, socket, socket.fileno())
        self.unregister(socket.fileno(), force=True)
        self.handle_switch(gl.switch())

    def handle_switch(self, rec):
        log.debug("ioloop.handle_switch %r", rec)
        # switch on type
        getattr(self, 'socket_' + rec[0])(*rec[1:])

    def run(self):
        log.debug("ioloop.run")
        self.handle_switch(self.parent.switch())
        while True:
            # TODO: is this needed?
            #if not len(self.registered):
            #    log.debug("nothing to poll, switching to parent")
            #    self.parent.switch()
            #    continue

            log.debug("polling")
            events = self.poll.poll()
            for fileno, event in events:
                log.debug("event %r %r", fileno, event)

                # TODO: needed? What does this mean exactly? Should no more events be processed?
                if event & select.POLLHUP:
                    log.debug("POLLHUP %r %r", fileno, event)
                    self.unregister(fileno, force=True)

                elif event & select.POLLIN:
                    if 'recv' in self.registered[fileno]['operations']:
                        r = self.registered[fileno]['operations']['recv']
                        self.do_recv(r)

                    elif 'accept' in self.registered[fileno]['operations']:
                        r = self.registered[fileno]['operations']['accept']
                        self.do_accept(r)

                    else:
                        log.info("Received POLLIN for unregistered fd %r, ignoring", fileno)
                        #raise Exception("Got event %r for %r but not in to_recv and to_accept" % (event, fileno))

                elif event & select.POLLOUT:
                    if 'send' in self.registered[fileno]['operations']:
                        r = self.registered[fileno]['operations']['send']
                        self.do_send(r)
                    else:
                        log.info("Received POLLOUT for unregistered fd %r, ignoring", fileno)

coreloop = ioloop()
coreloop.switch()
