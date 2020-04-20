from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_safe

from kuma.core.decorators import header
from kuma.wiki import kumascript


@header("X-Robots-Tag", "noindex,nofollow")
@never_cache
@require_safe
def revision_hash(request):
    """
    Return the kuma revision hash.
    """
    return HttpResponse(
        settings.REVISION_HASH, content_type="text/plain; charset=utf-8"
    )


@header("X-Robots-Tag", "noindex,nofollow")
@never_cache
@require_safe
def kumascript_revision_hash(request):
    """
    Return the kumascript revision hash. Requests the value directly
    from the kumascript service.
    """
    ks_response = kumascript.request_revision_hash()
    return HttpResponse(
        ks_response.text,
        status=ks_response.status_code,
        content_type=ks_response.headers.get("content-type"),
    )
