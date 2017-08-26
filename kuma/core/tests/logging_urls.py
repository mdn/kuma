from django.conf.urls import url
from django.core.exceptions import SuspiciousOperation


def suspicious(request):
    raise SuspiciousOperation('Raising exception to test logging.')


urlpatterns = [
    url(r'^suspicious/$',
        suspicious,
        name='suspicious'),
]
