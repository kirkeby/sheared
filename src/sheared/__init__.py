#
# Sheared -- non-blocking network programming library for Python
# Copyright (C) 2003  Sune Kirkeby
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

FIXME -- I am not entirely pleased with this text.

This module contains all the different components of Sheared, right now
this includes:

- sheared.reactor and sheared.reactors

The reactor is a low-level network programming library for Python (in
general it should be able to do any I/O you need, but it makes most
sense in networked programs).  It is built on top of Stackless Python,
and instead of threads and blocking I/O Sheared uses Stackless
tasklets and asynchronous I/O. But, apart from other asynchronous
network libraries, programming the Sheared reactor is almost
entirely like programming a normal blocking network library.

- sheared.web

A web-server programming library built on the Sheared reactor. The
design is meant to be general enough that you could write for instance a
WebDAV server on top of it, but at the same time you can just point it
at a directory, and it will happily serve up all files underneeth (see
doc/examples/web/filesystem in the source tree). Of course you can also
serve up dynamic resources.

- sheared.protocol

All manner of helpers for writing clients and servers for various
networking protocols, currently the HTTP/1.0 and PostgreSQL protocols
are implmented.

- sheared.python

Helpers for various things related to network and daemon programming
with Sheared (e.g. a logging infrastructure and helpers for daemonizing)."""

import sheared.reactors.greenlet
reactor = sheared.reactors.greenlet.Reactor()

__author__ = 'Sune Kirkeby'
__version__ = '0.1'

__all__ = ['python', 'reactor', 'reactors', 'protocol',
           'database', 'web', 'error']
