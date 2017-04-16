from __future__ import absolute_import

from django.conf.urls.defaults import (patterns, include, url,  # noqa
                                       handler500, handler404)
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    # Uncomment the admin/doc line below and add 'django.contrib.admindocs'
    # to INSTALLED_APPS to enable admin documentation:
    (r'^doc/', include('django.contrib.admindocs.urls')),

    (r'', include(admin.site.urls)),
)
