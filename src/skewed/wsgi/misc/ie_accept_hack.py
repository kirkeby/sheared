__all__ = ['IEAcceptHack']

bad_user_agents = [
    'Mozilla/4.0 (compatible; MSIE ',
    'Googlebot/',
]
def is_bad(environ):
    ua = environ.get('HTTP_USER_AGENT', '')
    if not ua:
        return 0
    for bad in bad_user_agents:
        if ua.startswith(bad):
            return 1
    return 0

class IEAcceptHack:
    def __init__(self, application):
        self.application = application

    def __call__(self, environ, start_response):
        def _start_response(status, headers):
            if is_bad(environ):
                headers = list(headers)
                for i in range(len(headers)):
                    if headers[i][0].lower() == 'content-type':
                        if headers[i][1] == 'application/xhtml+xml':
                            headers[i] = (headers[i][0], 'text/html')
                        elif headers[i][1].startswith('application/xhtml+xml;'):
                            _, params = headers[i][1].split(';', 1)
                            headers[i] = (headers[i][0], 'text/html;' + params)

            vary_found = 0
            for i in range(len(headers)):
                if headers[i][0].lower() == 'vary':
                    if not 'user-agent' in headers[i][1].lower().split():
                        headers[i] = headers[i][0], headers[i][1] + ' User-Agent'
                    vary_found = 1
            if not vary_found:
                headers.append(('Vary', 'User-Agent'))

            return start_response(status, headers)

        return self.application(environ, _start_response)
