# vim:nowrap:textwidth=0
#
# Sheared -- non-blocking network programming library for Python
# Copyright (C) 2003  Sune Kirkeby <sune@mel.interspace.dk>
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

from py.magic import greenlet

import os
import select

# dummy object for detecting dead greenlets
dummy = object()

class Reactor:
    def __init__(self):
        # state of reactor, is 'stopped', 'running' or 'stopping'
        self.state = 'stopped'
        # mapping selected file descriptors to greenlets
        self.fd_greenlet = {}
        # file descriptors sets to select on
        self.reading, self.writing = [], []
        
    def start(self, f):
        if not self.state == 'stopped':
            raise AssertionError, 'reactor not stopped'

        try:
            self.state = 'running'
            self.__bootstrap(f)
            self.__mainloop()
            self.__cleanup()
            self.state = 'stopped'
        except:
            self.state = 'b0rked'
            raise

    def stop(self):
        self.state = 'stopping'

    def read(self, fd, max):
        self.__wait_on_io(fd, self.reading)
        return os.read(fd, max)
    def write(self, data):
        self.__wait_on_io(fd, self.writing)
        return os.write(fd, data)

    def __wait_on_io(self, fd, list):
        g = greenlet.getcurrent()
        self.fd_greenlet[fd] = g
        list.append(fd)
        result = g.parent.switch()
        list.remove(fd)
        del self.fd_greenlet[fd]

        if not result is dummy:
            raise result

    def __bootstrap(self, f):
        g = greenlet(f)
        g.switch(self)

    def __mainloop(self):
        while self.state == 'running':
            if not self.reading or self.writing:
                break
            self.__select(None)

    def __cleanup(self):
        # FIXME -- this code-path is untested
        for fd in self.reading + self.writing:
            g = self.fd_greenlet[fd]
            g.switch(RuntimeError('reactor is shutting down'))

        self.fd_greenlet = {}
        self.reading, self.writing = [], []

    def __select(self, timeout):
        r, w, e = select.select(self.reading, self.writing, [], timeout)

        for fd in r + w + e:
            g = self.fd_greenlet[fd]
            # if the greenlet is dead this switches back to g.parent
            # (i.e. here), we use dummy to detect this
            if g.switch(dummy) is dummy:
                # FIXME -- this code-path is untested
                raise AssertionError, 'greenlet is dead: %s' % g
        
__all__ = ['Reactor']
