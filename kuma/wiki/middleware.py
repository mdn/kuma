

from django.shortcuts import render
from django.views.decorators.cache import never_cache

from kuma.core.middleware import MiddlewareBase

from .exceptions import ReadOnlyException


class ReadOnlyMiddleware(MiddlewareBase):
    """
    Renders a 403.html page with a flag for a specific message.
    """

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if isinstance(exception, ReadOnlyException):
            context = {'reason': exception.args[0]}
            return never_cache(render)(request, '403.html', context,
                                       status=403)
        return None
