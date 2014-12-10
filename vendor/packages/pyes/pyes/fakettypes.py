#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Alberto Paro'

#
# Fake ttypes to use in http protocol to simulate thrift ones
#

class Method:
    GET = 0
    PUT = 1
    POST = 2
    DELETE = 3
    HEAD = 4
    OPTIONS = 5

    _VALUES_TO_NAMES = {
                        0: "GET",
                        1: "PUT",
                        2: "POST",
                        3: "DELETE",
                        4: "HEAD",
                        5: "OPTIONS",
        }

    _NAMES_TO_VALUES = {
                        "GET": 0,
                        "PUT": 1,
                        "POST": 2,
                        "DELETE": 3,
                        "HEAD": 4,
                        "OPTIONS": 5,
                      }

class Status:
    CONTINUE = 100
    SWITCHING_PROTOCOLS = 101
    OK = 200
    CREATED = 201
    ACCEPTED = 202
    NON_AUTHORITATIVE_INFORMATION = 203
    NO_CONTENT = 204
    RESET_CONTENT = 205
    PARTIAL_CONTENT = 206
    MULTI_STATUS = 207
    MULTIPLE_CHOICES = 300
    MOVED_PERMANENTLY = 301
    FOUND = 302
    SEE_OTHER = 303
    NOT_MODIFIED = 304
    USE_PROXY = 305
    TEMPORARY_REDIRECT = 307
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    PAYMENT_REQUIRED = 402
    FORBIDDEN = 403
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    NOT_ACCEPTABLE = 406
    PROXY_AUTHENTICATION = 407
    REQUEST_TIMEOUT = 408
    CONFLICT = 409
    GONE = 410
    LENGTH_REQUIRED = 411
    PRECONDITION_FAILED = 412
    REQUEST_ENTITY_TOO_LARGE = 413
    REQUEST_URI_TOO_LONG = 414
    UNSUPPORTED_MEDIA_TYPE = 415
    REQUESTED_RANGE_NOT_SATISFIED = 416
    EXPECTATION_FAILED = 417
    UNPROCESSABLE_ENTITY = 422
    LOCKED = 423
    FAILED_DEPENDENCY = 424
    INTERNAL_SERVER_ERROR = 500
    NOT_IMPLEMENTED = 501
    BAD_GATEWAY = 502
    SERVICE_UNAVAILABLE = 503
    GATEWAY_TIMEOUT = 504
    INSUFFICIENT_STORAGE = 506

    _VALUES_TO_NAMES = {
      100: "CONTINUE",
      101: "SWITCHING_PROTOCOLS",
      200: "OK",
      201: "CREATED",
      202: "ACCEPTED",
      203: "NON_AUTHORITATIVE_INFORMATION",
      204: "NO_CONTENT",
      205: "RESET_CONTENT",
      206: "PARTIAL_CONTENT",
      207: "MULTI_STATUS",
      300: "MULTIPLE_CHOICES",
      301: "MOVED_PERMANENTLY",
      302: "FOUND",
      303: "SEE_OTHER",
      304: "NOT_MODIFIED",
      305: "USE_PROXY",
      307: "TEMPORARY_REDIRECT",
      400: "BAD_REQUEST",
      401: "UNAUTHORIZED",
      402: "PAYMENT_REQUIRED",
      403: "FORBIDDEN",
      404: "NOT_FOUND",
      405: "METHOD_NOT_ALLOWED",
      406: "NOT_ACCEPTABLE",
      407: "PROXY_AUTHENTICATION",
      408: "REQUEST_TIMEOUT",
      409: "CONFLICT",
      410: "GONE",
      411: "LENGTH_REQUIRED",
      412: "PRECONDITION_FAILED",
      413: "REQUEST_ENTITY_TOO_LARGE",
      414: "REQUEST_URI_TOO_LONG",
      415: "UNSUPPORTED_MEDIA_TYPE",
      416: "REQUESTED_RANGE_NOT_SATISFIED",
      417: "EXPECTATION_FAILED",
      422: "UNPROCESSABLE_ENTITY",
      423: "LOCKED",
      424: "FAILED_DEPENDENCY",
      500: "INTERNAL_SERVER_ERROR",
      501: "NOT_IMPLEMENTED",
      502: "BAD_GATEWAY",
      503: "SERVICE_UNAVAILABLE",
      504: "GATEWAY_TIMEOUT",
      506: "INSUFFICIENT_STORAGE",
    }

    _NAMES_TO_VALUES = {
      "CONTINUE": 100,
      "SWITCHING_PROTOCOLS": 101,
      "OK": 200,
      "CREATED": 201,
      "ACCEPTED": 202,
      "NON_AUTHORITATIVE_INFORMATION": 203,
      "NO_CONTENT": 204,
      "RESET_CONTENT": 205,
      "PARTIAL_CONTENT": 206,
      "MULTI_STATUS": 207,
      "MULTIPLE_CHOICES": 300,
      "MOVED_PERMANENTLY": 301,
      "FOUND": 302,
      "SEE_OTHER": 303,
      "NOT_MODIFIED": 304,
      "USE_PROXY": 305,
      "TEMPORARY_REDIRECT": 307,
      "BAD_REQUEST": 400,
      "UNAUTHORIZED": 401,
      "PAYMENT_REQUIRED": 402,
      "FORBIDDEN": 403,
      "NOT_FOUND": 404,
      "METHOD_NOT_ALLOWED": 405,
      "NOT_ACCEPTABLE": 406,
      "PROXY_AUTHENTICATION": 407,
      "REQUEST_TIMEOUT": 408,
      "CONFLICT": 409,
      "GONE": 410,
      "LENGTH_REQUIRED": 411,
      "PRECONDITION_FAILED": 412,
      "REQUEST_ENTITY_TOO_LARGE": 413,
      "REQUEST_URI_TOO_LONG": 414,
      "UNSUPPORTED_MEDIA_TYPE": 415,
      "REQUESTED_RANGE_NOT_SATISFIED": 416,
      "EXPECTATION_FAILED": 417,
      "UNPROCESSABLE_ENTITY": 422,
      "LOCKED": 423,
      "FAILED_DEPENDENCY": 424,
      "INTERNAL_SERVER_ERROR": 500,
      "NOT_IMPLEMENTED": 501,
      "BAD_GATEWAY": 502,
      "SERVICE_UNAVAILABLE": 503,
      "GATEWAY_TIMEOUT": 504,
      "INSUFFICIENT_STORAGE": 506,
    }

class RestRequest:
    """
    Attributes:
     - method
     - uri
     - parameters
     - headers
     - body
    """

    def __init__(self, method=None, uri=None, parameters=None, headers=None, body=None,):
        self.method = method
        self.uri = uri
        self.parameters = parameters
        self.headers = headers
        self.body = body

class RestResponse:
    """
    Attributes:
     - status
     - headers
     - body
    """
    def __init__(self, status=None, headers=None, body=None,):
        self.status = status
        self.headers = headers
        self.body = body


