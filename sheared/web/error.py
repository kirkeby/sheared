from sheared.protocol.http import HTTP_NOT_FOUND, \
                                  HTTP_UNAUTHORIZED, \
                                  HTTP_FORBIDDEN, \
                                  HTTP_MOVED_PERMANENTLY, \
                                  HTTP_BAD_REQUEST, \
                                  HTTP_INTERNAL_SERVER_ERROR

class WebServerError(Exception):
    statusCode = HTTP_INTERNAL_SERVER_ERROR

class InputError(WebServerError):
    statusCode = HTTP_BAD_REQUEST

class UnauthorizedError(WebServerError):
    statusCode = HTTP_UNAUTHORIZED
class ForbiddenError(WebServerError):
    statusCode = HTTP_FORBIDDEN

class NotFoundError(WebServerError):
    statusCode = HTTP_NOT_FOUND

class MovedPermanently(WebServerError):
    statusCode = HTTP_MOVED_PERMANENTLY

__all__ = ['WebServerError', 'UnauthorizedError', 'ForbiddenError',
    'NotFoundError', 'MovedPermanently']
