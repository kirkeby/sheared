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
"""Simpleminded implementation of min-queue."""

class MinQueue:
    def __init__(self):
        self.queued = []

    def minkey(self):
        return self.queued[0][0]

    def getmin(self):
        return self.queued.pop(0)[1]

    def insert(self, key, value):
        i = 0
        for i in range(len(self.queued)):
            if self.queued[i][0] > key:
                break
        self.queued.insert(i, (key, value))

    def empty(self):
        return len(self.queued) == 0

__all__ = ['MinQueue']
