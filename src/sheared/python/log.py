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

import os
import sys
import time
import traceback
import types

dangerous_in_logs = range(0, 33) + range(128, 156)
dangerous_in_logs.remove(ord('\n'))
dangerous_in_logs.remove(ord('\t'))
dangerous_in_logs.remove(ord(' '))
def escape_dangerous(s):
    s = s.replace('\\', '\\\\')
    for c in dangerous_in_logs:
        s = s.replace(chr(c), '\\x%02x' % c)
    return s

class Log:
    def timestamped(self, s):
        s = escape_dangerous(s)
        lines = s.split('\n')
        prefix = self._prefix(None)
        lines = ['%s%s' % (prefix, line) for line in lines]
        self.write('\n'.join(lines) + '\n')
        
    def prefixed(self, s, p):
        s = escape_dangerous(s)
        lines = s.split('\n')
        prefix = self._prefix(p)
        lines = ['%s%s' % (prefix, line) for line in lines]
        self.write('\n'.join(lines) + '\n')

    def debug(self, s):
        self.prefixed(s, 'debug')
        
    def normal(self, s):
        self.prefixed(s, 'normal')
    
    def exception(self, ex):
        assert type(ex) is types.TupleType and len(ex) == 3, `ex`
        lines = [self._prefix('exception')]
        for thing in traceback.format_exception(ex[0], ex[1], ex[2]):
            thing = [ '\t' + line for line in thing.split('\n')[:-1] ]
            lines.extend(thing)
        self.write('\n'.join(lines) + '\n')

    def showwarning(self, message, category, filename, lineno, file=None):
        line = '%s in %s:%d; %s' % (category, filename, lineno, message)
        self.write(self._prefix('warning') + line + '\n')
    
    def _prefix(self, cls):
        prefix = '[%s] [%d] ' % (time.ctime(), os.getpid())
        if cls:
            prefix = prefix + '[%s] ' % cls
        return prefix

class StderrLog(Log): # sounds a bit like StdAirlock...
    def close(self):
        pass
    def write(self, s):
        return sys.stderr.write(s)

default = StderrLog()
def showwarning(*a):
    default.showwarning(*a)

__all__ = ['default', 'showwarning']
