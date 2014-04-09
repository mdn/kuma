"""
URL patterns for testing our custom error handlers.

"""

from django.conf.urls import patterns
from django.conf.urls import url

from devmo.views import error_page


urlpatterns = patterns('',
    url(r'^error_403/',
        lambda r: error_page(r, 403),
        name='test_error_403'),
    url(r'^error_404/',
        lambda r: error_page(r, 404),
        name='test_error_404'),
    url(r'^error_500/',
        lambda r: error_page(r, 500),
        name='test_error_500'),
)
