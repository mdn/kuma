from django.http import HttpResponseForbidden

from .views import handle403


class Forbidden403Middleware(object):
    """
    Renders a 403.html page if response.status_code == 403.
    """
    def process_response(self, request, response):
        if isinstance(response, HttpResponseForbidden):
            return handle403(request)
        # If not 403, return response unmodified
        return response
