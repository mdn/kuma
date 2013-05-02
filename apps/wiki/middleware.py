from django.shortcuts import render

from wiki import ReadOnlyException


class ReadOnlyMiddleware(object):
    """
    Renders a 403.html page with a flag for a specific message.
    """
    def process_exception(self, request, exception):
        if isinstance(exception, ReadOnlyException):
            return render(request, '403.html',
                                {'reason': exception.args[0]},
                                status=403)
        return None
