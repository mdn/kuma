from django.core.exceptions import SuspiciousOperation
from django.urls import re_path

from kuma.core.urlresolvers import i18n_patterns


def suspicious(request):
    raise SuspiciousOperation("Raising exception to test logging.")


urlpatterns = i18n_patterns(re_path(r"^suspicious/$", suspicious, name="suspicious"))
