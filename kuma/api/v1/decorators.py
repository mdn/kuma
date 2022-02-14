from functools import wraps

from django.http import HttpResponseForbidden

from .auth import NotASubscriber, is_subscriber


def allow_CORS_GET(func):
    """Decorator to allow CORS for GET requests"""

    @wraps(func)
    def inner(request, *args, **kwargs):
        response = func(request, *args, **kwargs)
        if "GET" == request.method:
            response["Access-Control-Allow-Origin"] = "*"
        return response

    return inner


def require_subscriber(view_function):
    """Check if a user is authorized to retrieve a resource.

    * Check if a user is logged in through kuma (django session).
    * Check if there is a bearer token in the request header.
      - Validate the token.
      - Create a new user if there is not one
      - Retrieve the resource for that user
    """

    @wraps(view_function)
    def is_authorized(request, *args, **kwargs):
        try:
            assert is_subscriber(request, raise_error=True)
        except NotASubscriber as e:
            return HttpResponseForbidden(e)
        return view_function(request, *args, **kwargs)

    return is_authorized
