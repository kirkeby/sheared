import sys
import glob
import re
import os
import os.path
import mimetypes
import logging
import entwine
import warnings

from sheared.web.querystring import HTTPQueryString
from sheared.web import cookie

from skewed.wsgi.misc import relative
from skewed.wsgi.misc import choose_widget
from skewed.wsgi.misc import accept

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
        self.index = 'index'

        self.doctypes = {
            'text/xml': "<?xml version='1.0' charset='utf-8'?>\r\n",
            'application/xml': "<?xml version='1.0' charset='utf-8'?>\r\n",
            'application/xhtml+xml':
                "<?xml version='1.0' charset='utf-8'?>\r\n"
                '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"\r\n'
                '          "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">\r\n',
            'text/html':
                '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN"\r\n'
                '          "http://www.w3.org/TR/html4/strict.dtd">\r\n',
        }

        self.load_templates()

    def load_templates(self):
        self.templates = {}
        for path in glob.glob(os.path.join(self.templates_path, '*.xhtml')):
            try:
                template = open(path).read()
                compiled = entwine.metal.compile(template, entwine.tales)
                entwine.metal.execute(compiled, self.templates)
            except:
                warnings.warn('Could not load %s' % path)
    
    def __call__(self, environ, start_response):
        path_info = environ['PATH_INFO']
        if path_info.endswith('/'):
            path_info = environ['PATH_INFO'] = path_info + self.index

        if not re_good_path_info.match(path_info):
            start_response('403 Forbidden',
                           [('Content-Type', 'text/plain')])
            return ['Malformed path requested.']

        static = self.as_static(environ, start_response)
        if not static is None:
            return static

        return self.as_pypage(environ, start_response)

    def as_static(self, environ, start_response):
        path_info = environ['PATH_INFO']

        static = self.static_path + path_info
        path, headers = None, None

        # First, see if the exact path requested exists
        if os.access(static, os.R_OK):
            path, headers = static, {}

        # If not, do the multiview-dance
        else:
            widgets = {}
            for possible in glob.glob(static + '*'):
                ct, ce = mimes.guess_type(possible)
                if not ct:
                    continue
                widgets[possible] = { 'Vary': 'Accept', 'Content-Type': ct }

            path = accept.choose_widget(environ, widgets.items())
            if path:
                headers = widgets[path]

        # Serve the chosen file (if any)
        if path is None:
            return None

        elif os.path.isdir(path):
            loc = relative('', environ)
            start_response('301 Moved Permanently',
                           [('Content-Type', 'text/plain'),
                            ('Location', loc),])
            return ['Moved here: %s.' % loc]
        
        elif os.path.isfile(path):
            ct, ce = mimes.guess_type(path)
            if ct and not headers.has_key('Content-Type'):
                headers['Content-Type'] = ct
            if ce and not headers.has_key('Content-Encoding'):
                headers['Content-Encoding'] = ce
            
            start_response('200 Ok', headers.items())
            return [open(path).read()]

        else:
            start_response('410 Forbidden', [('Content-Type', 'text/plain')])
            return ['Not allowed.']

    def as_pypage(self, environ, start_response):
        path_info = environ['PATH_INFO']

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
        namespace = {
            'ZPTView': ZPTView,
            'BaseController': BaseController,
            'Cookie': cookie.Cookie,
        }
        eval(code, namespace)

        # get controller and view for this page
        controller = namespace.get('Controller', DefaultController)(self)
        view = namespace.get('View', DefaultView)(self)
        
        # handle arguments
        context = controller.process(request, reply)

        # render view
        result = view.render(context, request, reply)
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

        self.cookies = {}
        baked = self.environ.get('HTTP_COOKIE', '')
        if baked:
            for b in baked.split(';'):
                c = cookie.parse(b)
                self.cookies[c.name] = c

class Reply:
    def __init__(self, status, headers):
        self.status = status
        self.headers = headers

class BaseController:
    def __init__(self, app):
        self.application = app
    def process(self, request, reply):
        return { 'here': { 'templates': self.application.templates } }
class DefaultController(BaseController):
    pass
class ZPTView:
    def __init__(self, application):
        self.application = application
        self.model = self.application.model
        self.template_extensions = ['.xhtml', '.xml', '.html']
    def massage(self, context):
        raise NotImplementedError, 'ZPTView.massage'
    def render(self, context, request, reply):
        path_info = request.environ['PATH_INFO']
        for ext in self.template_extensions:
            template = self.application.pages_path + path_info + ext
            if os.access(template, os.R_OK):
                break
        else:
            return ['Action completed, but no view was found.']

        ct, ce = mimes.guess_type(template)
        assert not ce
        header = 'Content-Type', ct + '; charset=utf-8'
        reply.headers.append(header)

        self.massage(context)
        body = entwine.entwine(open(template).read(), context).encode('utf-8')
        result = [body]
        if self.application.doctypes.has_key(ct):
            result.insert(0, self.application.doctypes[ct])
        return result
class DefaultView(ZPTView):
    def massage(self, context):
        pass
