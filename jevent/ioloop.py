# Copyright: (c) 2012 Justin Patrin <papercrane@reversefold.com>

import logging
from greenlet import greenlet
import select
__socket__ = __import__('socket')
import sys

from jevent import JEventException

log = logging.getLogger(__name__)

noop = object()

IDLE = True
IDLE_WAIT = 500 if IDLE else None


def lim(s, l=50):
    ss = str(s)
    return s if len(ss) < l else (ss[:l / 2] + '...' + ss[-l / 2:])

class ioloop(greenlet):
    def __init__(self):
        log.debug("ioloop.__init__")
        super(ioloop, self).__init__()

        self.registered = {}
        self.calls_to_process = []
        self.poll = select.poll()

    def register(self, fileno, flag, operation):
        log.debug("ioloop.register %r %r %r", fileno, flag, operation)

        if fileno in self.registered:
            # TODO: given the way this is meant to be used could one socket really be registered for multiple operations?
            if operation in self.registered[fileno]['operations']:
                raise JEventException("%r already registered for operation %r %r" % (fileno, operation, flag))

            self.registered[fileno]['flags'] |= flag
            self.registered[fileno]['operations'][operation] = greenlet.getcurrent()
            self.poll.modify(fileno, self.registered[fileno]['flags'])

        else:
            self.registered[fileno] = {
                'operations': { operation: greenlet.getcurrent() },
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

    def run(self):
        if greenlet.getcurrent() != self:
            log.warn("Don't call ioloop.run() directly, call ioloop.switch() instead")
            self.switch()
            return
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
                        self.registered[fileno]['operations']['recv'].switch()

                    elif 'accept' in self.registered[fileno]['operations']:
                        self.registered[fileno]['operations']['accept'].switch()

                    else:
                        log.warn("Received POLLIN for unregistered fd %r, ignoring", fileno)
                        #raise Exception("Got event %r for %r but not in to_recv and to_accept" % (event, fileno))

                if event & select.POLLOUT:
                    if 'send' in self.registered[fileno]['operations']:
                        self.registered[fileno]['operations']['send'].switch()
                    else:
                        log.warn("Received POLLOUT for unregistered fd %r, ignoring", fileno)

                if event & select.POLLHUP:
                    log.debug("POLLHUP %r %r", fileno, event)
                    # when filenos are reused by the OS, we might receive a HUP for a fileno which was for its previous incarnation.....
                    #for operation, r in self.registered[fileno]['operations'].iteritems():
                    #    # this will have the side-effect of unregistering these calls due to socket._do_operation's finally clause
                    #    r['greenlet'].throw(__socket__.error("Connection closed"))
#            else:
#                # no events to process, let the parent greenlet run
#                self.parent.switch()
#            log.info("switch() to parent from ioloop")
            if IDLE:
                self.parent.switch(noop)

_coreloops = {}
def coreloop():
    import threading
    t = threading.current_thread()
    if t not in _coreloops:
        l = ioloop()
        _coreloops[t] = l
        top = greenlet.getcurrent()
        while top.parent:
            top = top.parent
        l.parent = top
        l.switch()
    return _coreloops[t]
