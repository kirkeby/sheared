"""Sheared non-blocking network programming library for Python.

Sheared is a low-level network programming library for Python (in general it
should be able to do any I/O you need, but it makes most sense in networked
programs).  It is built on top of py.magic.greenlet and select, and instead of
threads and blocking I/O, Sheared uses greenlets and asynchronous I/O.
"""

__author__ = 'Sune Kirkeby'
__version__ = '0.1'

__all__ = ['Reactor', 'TimeoutError']

from sheared.error import *

from sheared.core import Reactor
reactor = Reactor()
