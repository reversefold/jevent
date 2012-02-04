__time__ = __import__('time')

from jevent import ioloop

IDLE_SLEEP = 0.01

class timerloop(object):
    def __init__(self, coreloop):
        self.coreloop = coreloop

    def wait(self, secs):
        if secs <= 0:
            # TODO: do we want to register, switch, and let it switch back?
            return
        mint = min(IDLE_SLEEP, secs)
        self.coreloop.register_listener()
        while secs > 0:
            pretime = __time__.time()
            if self.coreloop.switch():
                __time__.sleep(mint)
            secs -= __time__.time() - pretime
        self.coreloop.unregister_listener()

_timerloops = {}
def timer():
    import threading
    t = threading.current_thread()
    if t not in _timerloops:
        l = timerloop(ioloop.coreloop())
        _timerloops[t] = l
    return _timerloops[t]

def sleep(secs):
    timer().wait(secs)
