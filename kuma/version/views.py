import os

from django.http import HttpResponse
from django.views.decorators.http import require_safe

from kuma.wiki import kumascript


@require_safe
def revision_hash(request):
    """
    Return the kuma revision hash.
    """
    return HttpResponse(
        os.getenv('REVISION_HASH', 'undefined'),
        content_type='text/plain; charset=utf-8'
    )


@require_safe
def kumascript_revision_hash(request):
    """
    Return the kumascript revision hash. Requests the value directly
    from the kumascript service.
    """
    response = kumascript.request_revision_hash()
    return HttpResponse(
        response.text,
        status=response.status_code,
        content_type=response.headers.get('content-type')
    )
