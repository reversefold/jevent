import logging
from greenlet import greenlet
import select

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
        if fileno == -1:
            log.error("fileno is -1")
            import pdb;pdb.set_trace()

        log.debug("ioloop.register %r %r", fileno, flag)
        self.poll.register(fileno, select.POLLIN)
        self.registered[fileno] = self.registered.get(fileno, 0) | flag

    def unregister(self, fileno, flag):
        if fileno not in self.registered:
            return
        log.debug("ioloop.unregister %r %r", fileno, flag)
        r = self.registered[fileno]
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
        self.to_recv[socket.fileno()] = (gl, socket, args, kwargs)
        self.register(socket.fileno(), select.POLLIN)

    def do_recv(self, r):
        try:
            data = r[1].socket.recv(*r[2], **r[3])
        except pysocket.error, e:
            if e.errno == 35: #Resource temporarily unavailable
                log.debug("Asynchronous socket has no readable data %r %r %r %r", fileno, event, r, e)
            else:
                raise
        else:
            log.debug("do_recv %r %r", data, r)
            self.unregister(r[1].fileno(), select.POLLIN)
            self.handle_switch(r[0].switch(data))

    def socket_send(self, gl, socket, args, kwargs):
        log.debug("ioloop.socket_send %r %r %r %r %r", gl, socket, socket.fileno(), args, kwargs)
        r = (gl, socket, args, kwargs)
        if not self.do_send(r):
            self.to_send[socket.fileno()] = r
            self.register(socket.fileno(), select.POLLOUT)

    def do_send(self, r):
        try:
            ret = r[1].socket.send(*r[2], **r[3])
        except pysocket.error, e:
            if e.errno == 35: #Resource temporarily unavailable
                log.debug("Asynchronous socket is not ready to send data %r %r", r, e)
            else:
                raise
        else:
            log.debug("do_send %r %r", ret, r)
            self.unregister(r[1].fileno(), select.POLLOUT)
            self.handle_switch(r[0].switch(ret))

    def socket_close(self, gl, socket):
        log.debug("ioloop.socket_close %r %r %r", gl, socket, socket.fileno())
#        self.poll.unregister(socket.fileno())
        if socket.fileno() in self.to_recv:
            del self.to_recv[socket.fileno()]
        self.handle_switch(gl.switch())

    def socket_accept(self, gl, socket, args, kwargs):
        log.debug("ioloop.accept %r %r %r %r %r", gl, socket, socket.fileno(), args, kwargs)
        self.to_accept[socket.fileno()] = (gl, socket, args, kwargs)
        self.register(socket.fileno(), select.POLLIN)

    def do_accept(self, r):
        data = r[1].socket.accept(*r[2], **r[3])
        log.debug("do_accept %r %r", data, r)
#        self.unregister(r[1].fileno(), select.POLLIN)
        self.handle_switch(r[0].switch(data))

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

                if event & select.POLLIN:
                    if fileno in self.to_recv:
                        r = self.to_recv[fileno]
                        self.do_recv(r)

                    else:
                        r = self.to_accept[fileno]
                        self.do_accept(r)

                elif event & select.POLLOUT:
                    r = self.to_send[fileno]
                    self.do_send(r)

                # TODO: needed?
                #elif event & select.POLLHUP:
                #    log.debug("POLLHUP %r %r", fileno, event)
                #    del self.to_recv[fileno]
                #    del self.to_send[fileno]

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
