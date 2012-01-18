import logging
from greenlet import greenlet
import select
pysocket = __import__('socket')
import sys

from jevent import JEventException

log = logging.getLogger(__name__)

noop = object()

IDLE = True
IDLE_WAIT = 100 if IDLE else None


def lim(s, l=50):
    ss = str(s)
    return s if len(ss) < l else (ss[:l] + '...')

class ioloop(greenlet):
    def __init__(self):
        log.debug("ioloop.__init__")
        super(ioloop, self).__init__()

        self.registered = {}
        self.calls_to_process = []
        self.poll = select.poll()

    def register(self, record, flag, operation):
        fileno = record['socket'].fileno()
        log.debug("ioloop.register %r %r", fileno, flag)
#        if fileno == -1:
#            log.error("fileno is -1")
#            import pdb;pdb.set_trace()

        if fileno in self.registered:
            # TODO: given the way this is meant to be used could one socket really be registered for multiple operations?
            if operation in self.registered[fileno]['operations']:
                raise JEventException("%r already registered for operation %r %r" % (fileno, operation, flag))

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
            log.warn("fileno not registered previously %r %r", fileno, flag)
            return
        
        r = self.registered[fileno]['flags']
        if force:
            r = 0
        else:
            r &= ~flag

        if r:
            log.debug("fileno unregistered flag %r %r %r", fileno, flag, lim(r))
            self.poll.modify(fileno, r)
            self.registered[fileno]['flags'] = r
            del self.registered[fileno]['operations'][operation]

        else:
            log.debug("fileno fully unregistered %r", fileno)
            self.poll.unregister(fileno)
            del self.registered[fileno]

#    def socket_recv(self, gl, socket, args, kwargs):
#        log.debug("ioloop.socket_recv %r %r %r %r %r", gl, socket, socket.fileno(), args, kwargs)
#        r = { 'greenlet': gl,
#              'socket': socket,
#              'args': args,
#              'kwargs': kwargs }
#        if not self.do_recv(r, False):
#            self.register(r, select.POLLIN, 'recv')
#
#    def do_recv(self, r, registered=True):
#        log.debug("ioloop.do_recv %r", r)
#        return self._do_socket_operation(r, registered, 'recv', select.POLLIN)
#
#    def socket_send(self, gl, socket, args, kwargs):
#        log.debug("ioloop.socket_send %r %r %r %r %r", gl, socket, socket.fileno(), args, kwargs)
#        r = { 'greenlet': gl,
#              'socket': socket,
#              'args': args,
#              'kwargs': kwargs}
#        if not self.do_send(r, False):
#            self.register(r, select.POLLOUT, 'send')
#
#    def do_send(self, r, registered=True):
#        log.debug("ioloop.do_send %r", r)
#        return self._do_socket_operation(r, registered, 'send', select.POLLOUT)
#
#    def _do_socket_operation(self, r, registered, operation, flag):
#        log.debug("ioloop._do_socket_operation %r %r %r %r", r, registered, operation, flag)
#        try:
#            ret = getattr(r['socket'].socket, operation)(*r['args'], **r['kwargs'])
#
#        except pysocket.error, e:
#            if e.errno == 35: #Resource temporarily unavailable
#                log.debug("Asynchronous socket is not ready for operation %r %r %r", operation, r, e)
#            else:
#                self._schedule_call(r['greenlet'].throw(*sys.exc_info()))
#
#        except:
#            self._schedule_call(r['greenlet'].throw(*sys.exc_info()))
#
#        else:
#            log.debug(" return %r %r", ret, r)
#            if registered:
#                self.unregister(r['socket'].fileno(), flag, operation)
#            self._schedule_call(r['greenlet'].switch(ret))
#            return True
#
#        return False
#
#    def socket_accept(self, gl, socket, args, kwargs):
#        log.debug("ioloop.accept %r %r %r %r %r", gl, socket, socket.fileno(), args, kwargs)
#        r = { 'greenlet': gl,
#              'socket': socket,
#              'args': args,
#              'kwargs': kwargs}
#        if not self.do_accept(r, False):
#            self.register(r, select.POLLIN, 'accept')
#
#    def do_accept(self, r, registered=True):
#        log.debug("ioloop.do_accept %r", r)
#        return self._do_socket_operation(r, registered, 'accept', select.POLLIN)
#
#    def socket_close(self, gl, socket):
#        log.debug("ioloop.socket_close %r %r %r", gl, socket, socket.fileno())
#        self.unregister(socket.fileno(), force=True)
#        self._schedule_call(gl.switch())
#
#    def _schedule_call(self, rec):
#        log.debug("ioloop._schedule_call %r", rec)
##        self.calls_to_process.append(rec)
##
##    def _process_call(self, rec):
##        log.debug("ioloop._process_call %r", rec)
#        # switch on type
#        getattr(self, 'socket_' + rec[0])(*rec[1:])

    def run(self):
        log.debug("ioloop.run")
#        self._schedule_call(self.parent.switch())
        self.parent.switch()
        while True:
#            for rec in self.calls_to_process:
#                self._process_call(rec)

            if IDLE and not self.registered:
                log.debug("nothing to poll, switching to parent")
                self.parent.switch(noop)
                continue

            log.debug("polling")
            events = self.poll.poll(IDLE_WAIT)
            for fileno, event in events:
                log.debug("event %r %r", fileno, event)

                # TODO: needed? What does this mean exactly? Should no more events be processed?
                #if event & select.POLLHUP:
                #    log.debug("POLLHUP %r %r", fileno, event)
                #    #self.unregister(fileno, force=True)
                #
                #elif event & select.POLLIN:
                if event & select.POLLIN:
                    if 'recv' in self.registered[fileno]['operations']:
                        r = self.registered[fileno]['operations']['recv']
                        r['greenlet'].switch(r['socket'].socket.recv(*r['args'], **r['kwargs']))
#                        self.do_recv(r)

                    elif 'accept' in self.registered[fileno]['operations']:
                        r = self.registered[fileno]['operations']['accept']
                        r['greenlet'].switch(r['socket'].socket.accept(*r['args'], **r['kwargs']))
#                        self.do_accept(r)

                    else:
                        log.info("Received POLLIN for unregistered fd %r, ignoring", fileno)
                        #raise Exception("Got event %r for %r but not in to_recv and to_accept" % (event, fileno))

                if event & select.POLLOUT:
                    if 'send' in self.registered[fileno]['operations']:
                        r = self.registered[fileno]['operations']['send']
                        r['greenlet'].switch(r['socket'].socket.send(*r['args'], **r['kwargs']))
#                        self.do_send(r)
                    else:
                        log.info("Received POLLOUT for unregistered fd %r, ignoring", fileno)

                if event & select.POLLHUP:
                    log.debug("POLLHUP %r %r", fileno, event)
                    #self.unregister(fileno, force=True)
#            else:
#                # no events to process, let the parent greenlet run
#                self.parent.switch()
#            log.info("switch() to parent from ioloop")
            if IDLE:
                self.parent.switch(noop)

coreloop = ioloop()
coreloop.switch()
