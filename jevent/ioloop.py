import logging
from greenlet import greenlet
import select
pysocket = __import__('socket')

log = logging.getLogger(__name__)

class ioloop(greenlet):
    def __init__(self):
        log.debug("ioloop.__init__")
        super(ioloop, self).__init__()

        self.registered = {}
        self.to_recv = {}
        self.to_send = {}
        self.to_accept = {}

        self.poll = select.poll()

    def register(self, fileno, flag):
        log.debug("ioloop.register %r %r", fileno, flag)
#        if fileno == -1:
#            log.error("fileno is -1")
#            import pdb;pdb.set_trace()

        self.poll.register(fileno, select.POLLIN)
        self.registered[fileno] = self.registered.get(fileno, 0) | flag

    def unregister(self, fileno, flag=None, force=False):
        log.debug("ioloop.unregister %r %r", fileno, flag)
        if fileno not in self.registered:
            log.debug("fileno not registered previously %r %r", fileno, flag)
            return
        r = self.registered[fileno]
        if force:
            r = 0
        else:
            r &= ~flag
        if r:
            log.debug("fileno unregistered flag %r %r %r", fileno, flag, r)
            self.poll.modify(fileno, r)
            self.registered[fileno] = r
        else:
            log.debug("fileno fully unregistered %r", fileno)
            self.poll.unregister(fileno)
            del self.registered[fileno]

    def socket_recv(self, gl, socket, args, kwargs):
        log.debug("ioloop.socket_recv %r %r %r %r %r", gl, socket, socket.fileno(), args, kwargs)
        r = (gl, socket, args, kwargs)
        if not self.do_recv(r):
            self.to_recv[socket.fileno()] = r
            self.register(socket.fileno(), select.POLLIN)

    def do_recv(self, r):
        log.debug("do_recv %r", r)
        try:
            data = r[1].socket.recv(*r[2], **r[3])

        except pysocket.error, e:
            if e.errno == 35: #Resource temporarily unavailable
                log.debug("Asynchronous socket has no readable data %r %r", r, e)
            else:
                self.handle_switch(r[0].throw(*sys.exc_info()))

        except:
            self.handle_switch(r[0].throw(*sys.exc_info()))             

        else:
            log.debug(" data %r %r", r, data)
            if r[1].fileno() in self.to_recv:
                del self.to_recv[r[1].fileno()]
            self.unregister(r[1].fileno(), select.POLLIN)
            log.info("recv, Switching to %r with %r", r, data)
            self.handle_switch(r[0].switch(data))
            return True

        return False

    def socket_send(self, gl, socket, args, kwargs):
        log.debug("ioloop.socket_send %r %r %r %r %r", gl, socket, socket.fileno(), args, kwargs)
        r = (gl, socket, args, kwargs)
        if not self.do_send(r):
            self.to_send[socket.fileno()] = r
            self.register(socket.fileno(), select.POLLOUT)

    def do_send(self, r):
        log.debug("do_send %r", r)
        try:
            ret = r[1].socket.send(*r[2], **r[3])

        except pysocket.error, e:
            if e.errno == 35: #Resource temporarily unavailable
                log.debug("Asynchronous socket is not ready to send data %r %r", r, e)
            else:
                self.handle_switch(r[0].throw(*sys.exc_info()))

        except:
            self.handle_switch(r[0].throw(*sys.exc_info()))             

        else:
            log.debug(" return %r %r", ret, r)
            log.info("send, Switching to %r with %r", r, ret)
            if r[1].fileno() in self.to_send:
                del self.to_send[r[1].fileno()]
            self.unregister(r[1].fileno(), select.POLLOUT)
            self.handle_switch(r[0].switch(ret))
            return True

        return False


    def socket_close(self, gl, socket):
        log.debug("ioloop.socket_close %r %r %r", gl, socket, socket.fileno())
        if socket.fileno() in self.to_recv:
            del self.to_recv[socket.fileno()]
        if socket.fileno() in self.to_send:
            del self.to_send[socket.fileno()]
        if socket.fileno() in self.to_accept:
            del self.to_accept[socket.fileno()]
        self.unregister(socket.fileno(), force=True)
        self.handle_switch(gl.switch())

    def socket_accept(self, gl, socket, args, kwargs):
        log.debug("ioloop.accept %r %r %r %r %r", gl, socket, socket.fileno(), args, kwargs)
        r = (gl, socket, args, kwargs)
        if not self.do_accept(r):
            self.to_accept[socket.fileno()] = r
            self.register(socket.fileno(), select.POLLIN)

    def do_accept(self, r):
        log.debug("do_accept %r", r)
        try:
             data = r[1].socket.accept(*r[2], **r[3])

        except pysocket.error, e:
            if e.errno == 35: #Resource temporarily unavailable
                log.debug("Asynchronous socket is not ready to accept %r %r", r, e)
            else:
                self.handle_switch(r[0].throw(*sys.exc_info()))

        except:
             self.handle_switch(r[0].throw(*sys.exc_info()))

        else:
            log.debug(" data %r %r", data, r)
            if r[1].fileno() in self.to_accept:
                del self.to_accept[r[1].fileno()]
            self.unregister(r[1].fileno(), select.POLLIN)
            log.info("accept, Switching to %r with %r", r, data)
            self.handle_switch(r[0].switch(data))
            return True

        return False

    def handle_switch(self, rec):
        log.debug("ioloop.handle_switch %r", rec)
        # switch on type
        getattr(self, 'socket_' + rec[0])(*rec[1:])

    def run(self):
        log.debug("ioloop.run")
        self.handle_switch(self.parent.switch())
        while True:
            # TODO: is this needed?
            #if not len(self.to_recv):
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
                    if fileno in self.to_recv:
                        del self.to_recv[fileno]
                    if fileno in self.to_send:
                        del self.to_send[fileno]
                    if fileno in self.to_accept:
                        del self.to_accept[fileno]
                    self.unregister(fileno, force=True)

                elif event & select.POLLIN:
                    if fileno in self.to_recv:
                        r = self.to_recv[fileno]
                        self.do_recv(r)

                    elif fileno in self.to_accept:
                        r = self.to_accept[fileno]
                        self.do_accept(r)

                    else:
                        log.info("Received POLLIN for unregistered fd %r, ignoring", fileno)
                        #raise Exception("Got event %r for %r but not in to_recv and to_accept" % (event, fileno))

                elif event & select.POLLOUT:
                    if fileno in self.to_send:
                        r = self.to_send[fileno]
                        self.do_send(r)
                    else:
                        log.info("Received POLLOUT for unregistered fd %r, ignoring", fileno)

#              if fileno == serversocket.fileno():
#                 connection, address = serversocket.accept()
#                 connection.setblocking(0)
#                 epoll.register(connection.fileno(), select.EPOLLIN)
#                 connections[connection.fileno()] = connection
#                 requests[connection.fileno()] = b''
#                 responses[connection.fileno()] = response
#              elif event & select.EPOLLIN:
#                 requests[fileno] += connections[fileno].recv(1024)
#                 if EOL1 in requests[fileno] or EOL2 in requests[fileno]:
#                    epoll.modify(fileno, select.EPOLLOUT)
#                    print('-'*40 + '\n' + requests[fileno].decode()[:-2])
#              elif event & select.EPOLLOUT:
#                 byteswritten = connections[fileno].send(responses[fileno])
#                 responses[fileno] = responses[fileno][byteswritten:]
#                 if len(responses[fileno]) == 0:
#                    epoll.modify(fileno, 0)
#                    connections[fileno].shutdown(socket.SHUT_RDWR)
#              elif event & select.EPOLLHUP:
#                 epoll.unregister(fileno)
#                 connections[fileno].close()
#                 del connections[fileno]

coreloop = ioloop()
coreloop.switch()
