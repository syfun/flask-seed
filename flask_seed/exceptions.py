# coding=utf-8

import sys

from flask import jsonify, current_app as app
import six


class ProjectException(Exception):
    """Base class for all exceptions."""
    message = "An unknown exception occurred."

    # make exception message format errors fatal
    fatal_exception_format_errors = False

    def __init__(self, message=None, **kwargs):
        self.kwargs = kwargs
        self.kwargs['message'] = message

        if self._should_format():
            try:
                message = self.message % kwargs
            except Exception:
                exc_info = sys.exc_info()
                # kwargs doesn't match a variable in the message
                # log the issue and the kwargs
                app.logger.exception('Exception in string format operation')
                for name, value in six.iteritems(kwargs):
                    app.logger.error("%(name)s: %(valule)s",
                                     {'name': name, 'value': value})
                if self.fatal_exception_format_errors:
                    six.reraise(*exc_info)
                # at least get the core message out if something happened
                message = self.message
        elif isinstance(message, Exception):
            message = six.text_type(message)

        # We put the actual message in 'msg' so that we can access
        # it, because if we try to access the message via 'message' it will be
        # overshadowed by the class' message attribute
        self.msg = message
        super(ProjectException, self).__init__(message)

    def _should_format(self):
        return self.kwargs['message'] is None or '%(message)' in self.message

    def __unicode__(self):
        return six.text_type(self.msg)

    def __str__(self):
        return six.text_type(self.msg)


class NotExist(ProjectException):
    """Not exist exception."""
    message = '%(resource)s %(id)s not exist.'


class NotNone(ProjectException):
    """Not none exception."""
    message = '%(resource)s %(key)s cannot be None.'


class DBError(ProjectException):
    """Database exception."""


class IDNotInt(DBError):
    """ID not integer."""
    message = 'ID must be integer.'


class HTTPError(ProjectException):
    status_code = 400

    def to_dict(self):
        return {'message': self.msg}


class HTTPBadRequest(HTTPError):
    status_code = 400
    message = '400 Bad Request.'


class HTTPUnauthorized(HTTPError):
    status_code = 401
    message = '401 Unauthorized.'


class HTTPForbidden(HTTPError):
    status_code = 403
    message = '403 Forbidden.'


class HTTPNotFound(HTTPError):
    status_code = 404
    message = '404 Not Found.'


class HTTPMethodNotAllowed(HTTPError):
    status_code = 405
    message = '405 Method Not Allowed.'


class HTTPInternalServerError(HTTPError):
    status_code = 500
    message = '500 Internal Server Error.'


def handle_http_error(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response
