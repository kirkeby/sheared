#!/usr/bin/env python
from distutils.core import setup, Extension
setup(name = "Sheared",
      version = "$Version: $",
      author = "Sune Kirkeby",
      url = "http://ibofobi.dk/stuff/sheared",
      packages = [
        'sheared', 'sheared.database', 'sheared.protocol',
        'sheared.python', 'sheared.reactors', 'sheared.web',
        'sheared.web.server', 'sheared.web.collections',
        'skewed', 'skewed.wsgi', 'skewed.wsgi.misc', 'skewed.web',
      ],
      package_dir = { '': 'src' },
      package_data = { 'sheared.web': ['test-docroot/*.*',
                                       'test-docroot/sub/.empty'],
                       'skewed.web': ['test-application/pages/*.py',
                                      'test-application/pages/*.xhtml',
                                      'test-application/templates/*.xhtml'],
                    },
      scripts = ['scripts/wsgi-httpd'],
    )
