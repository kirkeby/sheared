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

"""Sheared top-level module.

Sheared is a low-level network (I/O in general, really, but it makes
most sense in networked programs) programming library for Python. It is
built on top of Stackless Python, and instead of threads and blocking
I/O Sheared uses Stackless tasklets and asynchronous I/O. But, apart
from other asynchronous network libraries, programming Sheared is almost
entirely like programming a normal blocking network library."""

from sheared import reactors
reactor = reactors.default.Reactor()

__all__ = ['python', 'reactor', 'reactors', 'protocol',
           'database', 'web', 'error']
