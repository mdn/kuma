from functools import wraps

import newrelic.agent
from django.conf import settings


def allow_CORS_GET(func):
    """Decorator to allow CORS for GET requests"""

    @wraps(func)
    def _added_header(request, *args, **kwargs):
        response = func(request, *args, **kwargs)

        if "GET" == request.method:
            response["Access-Control-Allow-Origin"] = "*"
        return response

    return _added_header


@newrelic.agent.function_trace()
def process_document_path(func):
    """
    Decorator to process document_path into locale and slug.

    This function takes generic args and kwargs so it can presume as little
    as possible on the view method signature.
    """

    @wraps(func)
    def process(request, document_path=None, *args, **kwargs):
        # Set the kwargs that decorated methods will expect.
        kwargs["document_slug"] = document_path.rstrip("/")
        kwargs["document_locale"] = getattr(
            request, "LANGUAGE_CODE", settings.LANGUAGE_CODE
        )
        return func(request, *args, **kwargs)

    return process
