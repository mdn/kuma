from django.http import HttpResponse
from django.views.decorators.http import require_safe


@require_safe
def basic_health(request):
    """
    A successful response from this endpoint simply proves
    that Django is up and running. It doesn't mean that its
    supporting services (like MySQL, memcached, Celery) can
    be successfully used from within this service.
    """
    return HttpResponse(status=204)
