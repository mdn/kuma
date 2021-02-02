from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_safe


@never_cache
@require_safe
def revision_hash(request):
    """
    Return the kuma revision hash.
    """
    return HttpResponse(
        settings.REVISION_HASH, content_type="text/plain; charset=utf-8"
    )
