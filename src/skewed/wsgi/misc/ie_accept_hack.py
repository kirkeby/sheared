__all__ = ['IEAcceptHack']

def is_explorer(environ):
    return environ.get('HTTP_USER_AGENT', '').startswith('Mozilla/4.0 (compatible; MSIE ')

class IEAcceptHack:
    def __init__(self, application):
        self.application = application

    def __call__(self, environ, start_response):
        def _start_response(status, headers):
            if is_explorer(environ):
                headers = list(headers)
                for i in range(len(headers)):
                    if headers[i][0].lower() == 'content-type':
                        # FIXME -- handle parameters
                        if headers[i][1] == 'application/xhtml+xml':
                            headers[i] = (headers[i][0], 'text/html')
            return start_response(status, headers)
        # FIXME -- hack Accept header too
        return self.application(environ, _start_response)
