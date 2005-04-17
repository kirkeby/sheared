class Controller(BaseController):
    def process(self, request, reply):
        return { 'path-info': request.environ['PATH_INFO'] }
