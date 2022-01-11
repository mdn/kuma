from functools import wraps

from django.http import HttpResponseForbidden

from kuma.users.auth import is_authorized_request, KumaOIDCAuthenticationBackend


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
        user = request.user

        # If the user is logged in, allow access
        if user.is_authenticated:
            return view_function(request, *args, **kwargs)

        # if we are here, the user is not logged in
        # check if there is a bearer token in the header
        if access_token := request.META.get("HTTP_AUTHORIZATION"):
            payload = is_authorized_request(access_token)

            if error := payload.get("error"):
                return HttpResponseForbidden(error)

            # create user if there is not one
            request.user = KumaOIDCAuthenticationBackend.create_or_update_subscriber(
                payload
            )
            return view_function(request, *args, **kwargs)
        return HttpResponseForbidden("not signed in")

    return is_authorized
