# vim:syntax=python:textwidth=0
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


from distutils.core import setup, Extension
setup(name = "Sheared", version = "0.1",
      author = "Sune Kirkeby",
      url = "http://ibofobi.dk/stuff/sheared/",
      packages = [
        'sheared', 'sheared.database', 'sheared.protocol',
        'sheared.python', 'sheared.reactors', 'sheared.web',
        'sheared.web.server', 'sheared.web.collections',
        'skewed', 'skewed.wsgi', 'skewed.wsgi.misc', 'skewed.web',
      ],
      package_dir = { '': 'src' },
      package_data = { 'sheared.web': ['test-docroot/*.*',
                                       'test-docroot/sub/.empty'], },
    )
