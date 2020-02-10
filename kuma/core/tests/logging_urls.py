from django.conf.urls import url
from django.core.exceptions import SuspiciousOperation

from kuma.core.urlresolvers import i18n_patterns


def suspicious(request):
    raise SuspiciousOperation("Raising exception to test logging.")


urlpatterns = i18n_patterns(url(r"^suspicious/$", suspicious, name="suspicious"))
