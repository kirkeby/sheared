import sys
import glob
import re
import os
import os.path
import mimetypes
import logging
import entwine

from sheared.web.querystring import HTTPQueryString

from skewed.wsgi.misc import relative
from skewed.wsgi.misc import choose_widget

mimes = mimetypes.MimeTypes([ path for path in mimetypes.knownfiles
                              if os.access(path, os.R_OK) ])
mimes.add_type('application/xhtml+xml', '.xhtml')

template_content_types = [ 'application/xhtml+xml',
                           'application/xml',
                           'text/html' ]

re_good_path_info = re.compile('^/[a-zA-Z0-9_.-]+$')
class Pages:
    def __init__(self, path, context=None):
        self.path = path
        self.context = context or {}
        self.index = 'index'
    
    def __call__(self, environ, start_response):
        path_info = environ['PATH_INFO']
        if path_info == '/':
            start_response('301 Moved permanently',
                           [('Content-Type', 'text/plain'),
                            ('Location', relative(self.index, environ))])
            return ['Moved permanently.\r\n']

        if not re_good_path_info.match(path_info):
            start_response('403 Forbidden',
                           [('Content-Type', 'text/plain')])
            return ['Malformed path requested.']

        # Create list of (path, headers) for entities we can serve
        # for this request
        widgets = {}
        for path in glob.glob(self.path + path_info + '*'): # FIXME -- UNIX'ism
            if path.endswith('~'):
                continue
            if path.endswith('.py'):
                continue
            if not os.access(path, os.R_OK):
                continue

            ct, ce = mimes.guess_type(path)
            if not ct:
                continue

            widgets[path] = { 'Content-Type': ct }
            if ce:
                widgets[path]['Content-Encoding'] = ce

        if not widgets:
            start_response('404 Not found',
                           [('Content-Type', 'text/plain')])
            return ['The requested resource could not be found.\r\n']

        # Select which entity to serve based on the clients
        # Accept-headers
        widget = choose_widget(environ, widgets.items())
        if widget is None:
            start_response('406 Not Acceptable',
                           [('Content-Type', 'text/plain')])
            # FIXME -- return a list of available resources
            return ['No acceptable resource was found.']

        headers = widgets[widget]
        pywidget = os.path.splitext(widget)[0] + '.py'
        is_template = headers['Content-Type'] in template_content_types
        if is_template:
            context = {}
            context.update(self.context)
            request = Request(environ)
            reply = Reply('200 Ok', headers)

            if os.access(pywidget, os.R_OK):
                # load, compile and execute Python-code
                src = open(pywidget).read()
                code = compile(src, pywidget, 'exec')
                namespace = {}
                eval(code, namespace)

                # find and execute handler from Python-code
                handler = namespace['handler']
                handler(context, request, reply)
            
            # compile and execute template with context
            template = open(widget).read()
            document = entwine.entwine(template, context)
            
            # send result to client
            start_response(reply.status, reply.headers.items())
            return [document]

        else:
            start_response('200 Ok', headers.items())
            return open(path)

class Request:
    def __init__(self, environ):
        self.environ = environ

        method = environ['REQUEST_METHOD']
        content_type = environ.get('CONTENT_TYPE', None)
        if method == 'GET':
            self.query = HTTPQueryString(environ['QUERY_STRING'])
        elif method == 'POST' and content_type:
            if content_type == 'application/x-www-form-urlencoded':
                qs = environ['wsgi.input'].read()
                self.query = HTTPQueryString(qs)
        else:
            self.query = HTTPQueryString('')
class Reply:
    def __init__(self, status, headers):
        self.status = status
        self.headers = headers
