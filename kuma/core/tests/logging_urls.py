from django.conf.urls import url
from django.core.exceptions import SuspiciousOperation
from django.http import HttpResponseServerError


def handler500(request):
    return HttpResponseServerError('error')


def suspicious(request):
    raise SuspiciousOperation('Raising exception to test logging.')


urlpatterns = [
    url(r'^suspicious/$',
        suspicious,
        name='suspicious'),
]
