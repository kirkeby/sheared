#
# Sheared -- non-blocking network programming library for Python
# Copyright (C) 2003  Sune Kirkeby <sune@mel.interspace.dk>
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
from sheared.protocol.http import HTTP_NOT_FOUND, \
                                  HTTP_UNAUTHORIZED, \
                                  HTTP_FORBIDDEN, \
                                  HTTP_MOVED_PERMANENTLY, \
                                  HTTP_NOT_MODIFIED, \
                                  HTTP_NOT_ACCEPTABLE, \
                                  HTTP_BAD_REQUEST, \
                                  HTTP_INTERNAL_SERVER_ERROR, \
                                  HTTP_NOT_IMPLEMENTED

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

class NotAcceptable(WebServerError):
    statusCode = HTTP_NOT_ACCEPTABLE

class Moved(WebServerError):
    pass
class MovedPermanently(Moved):
    statusCode = HTTP_MOVED_PERMANENTLY
class NotModified(WebServerError):
    statusCode = HTTP_NOT_MODIFIED

class BadRequestError(WebServerError):
    statusCode = HTTP_BAD_REQUEST

class InternalServerError(WebServerError):
    statusCode = HTTP_INTERNAL_SERVER_ERROR

class NotImplementedError(WebServerError):
    statusCode = HTTP_NOT_IMPLEMENTED

__all__ = ['WebServerError', 'UnauthorizedError', 'ForbiddenError',
    'NotFoundError', 'MovedPermanently']
