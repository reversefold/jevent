JEvent
======

A library for using asynchronous network i/o while programming like it's synchronous i/o, written in pure python. Inspired by gevent.

The idea is to have a gevent-like library that can monkey-patch system libraries but written in pure python so it can work with pypy. The only dependency currently is greenlet, which is included in pypy-c by default now.
