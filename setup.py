# vim:syntax=python:textwidth=0

from distutils.core import setup, Extension
setup(name = "Sheared", version = "0.1",
      author = "Sune Kirkeby",
      author_email = "sune@mel.interspace.dk",
      url = "http://mel.interspace.dk/~sune/sheared/",
      packages = ['sheared', 'sheared.database', 'sheared.internet', 'sheared.protocol', 'sheared.python',
                             'sheared.reactor', 'sheared.web'],
      ext_modules = [Extension("sheared.python.fdpass", ["sheared/python/fdpass.c"])])
