from functools import wraps


def allow_CORS_GET(func):
    """Decorator to allow CORS for GET requests"""

    @wraps(func)
    def inner(request, *args, **kwargs):
        response = func(request, *args, **kwargs)
        if "GET" == request.method:
            response["Access-Control-Allow-Origin"] = "*"
        return response

    return inner
