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

re_good_path_info = re.compile('^/[a-zA-Z0-9_/-]+[.a-z0-9]*$')
class Pages:
    def __init__(self, model):
        self.model = model
        self.pages_path = 'pages'
        self.templates_path = 'templates'
        self.static_path = 'static'
        self.page_template_path = 'page.xhtml'
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

        static = self.static_path + path_info
        if os.access(static, os.R_OK):
            ct, ce = mimes.guess_type(static)
            headers = []
            if ct:
                headers.append(('Content-Type', ct))
            if ce:
                headers.append(('Content-Encoding', ce))
            
            start_response('200 Ok', headers)
            return open(static).read()

        pywidget = self.pages_path + path_info + '.py'
        if not os.access(pywidget, os.R_OK):
            start_response('404 Not Found',
                           [('Content-Type', 'text/plain')])
            return ['Path not found.']

        request = Request(environ)
        reply = Reply('200 Ok', [])

        # load, compile and execute Python-code
        src = open(pywidget).read()
        code = compile(src, pywidget, 'exec')
        namespace = {}
        eval(code, namespace)

        # get controller and view for this page
        controller = namespace.get('Controller', DefaultController)(self)
        view = namespace.get('View', DefaultView)(self)
        
        # handle arguments
        pass

        # render view
        result = view.render(request, reply)
        start_response('200 Ok', reply.headers)
        return result

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

class DefaultController:
    def __init__(self, application):
        pass
    def process(self, request):
        pass
class ZPTView:
    def __init__(self, application):
        self.application = application
        self.model = self.application.model
    def massage(self, context):
        raise NotImplementedError, 'ZPTView.massage'
    def render(self, request, reply):
        path_info = request.environ['PATH_INFO']
        template = self.application.templates_path + path_info + '.xhtml'
        if os.access(template, os.R_OK):
            ct = 'Content-Type', 'application/xhtml+xml; charset=utf-8'
            reply.headers.append(ct)

            context = {}
            page_template = os.path.join(self.application.templates_path,
                                         self.application.page_template_path)
            if os.access(page_template, os.R_OK):
                pt = open(page_template).read()
                pt = "<page metal:define-macro='page' tal:omit-tag='true'>%s</page>" % pt
                entwine.entwine(pt, context)
            else:
                pt = None

            t = open(template).read()
            if pt:
                t = "<page metal:use-macro='page'>%s</page>" % t
    
            self.massage(context)
            return [entwine.entwine(t, context)]

        else:
            return ['Action completed, but no view was found.']
class DefaultView(ZPTView):
    def massage(self, context):
        pass
