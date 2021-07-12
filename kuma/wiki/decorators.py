from functools import wraps


def allow_CORS_GET(func):
    """Decorator to allow CORS for GET requests"""

    @wraps(func)
    def _added_header(request, *args, **kwargs):
        response = func(request, *args, **kwargs)

        if "GET" == request.method:
            response["Access-Control-Allow-Origin"] = "*"
        return response

    return _added_header
