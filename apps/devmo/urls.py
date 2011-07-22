from django.conf.urls.defaults import *


urlpatterns = patterns('devmo.views',
    url(r'^events/?$', 'events', name='events'),
    url(r'^profiles/(?P<username>[^/]+)/$', 'profile_view',
        name="devmo_profile_view"),
    url(r'^profiles/(?P<username>[^/]+)/edit$', 'profile_edit',
        name="devmo_profile_edit"),
)
