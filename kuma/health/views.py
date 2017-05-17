from django.db import DatabaseError
from django.http import HttpResponse
from django.views.decorators.http import require_safe

from kuma.wiki.models import Document


@require_safe
def liveness(request):
    """
    A successful response from this endpoint simply proves
    that Django is up and running. It doesn't mean that its
    supporting services (like MySQL, memcached, Celery) can
    be successfully used from within this service.
    """
    return HttpResponse(status=204)


@require_safe
def readiness(request):
    """
    A successful response from this endpoint goes a step further
    and means not only that Django is up and running, but also that
    the database can be successfully used from within this service.
    The other supporting services are not checked, but we may find
    that we want/need to add them later.
    """
    try:
        # Confirm that we can use the database by making a fast query
        # against the Document table. It's not important that the document
        # with the requested primary key exists or not, just that the query
        # completes without error.
        Document.objects.filter(pk=1).exists()
    except DatabaseError as e:
        reason_tmpl = 'service unavailable due to database issue ({!s})'
        status, reason = 503, reason_tmpl.format(e)
    else:
        status, reason = 204, None
    return HttpResponse(status=status, reason=reason)
