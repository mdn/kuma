from django.conf.urls import patterns, url
import teamwork.views


urlpatterns = patterns('devmo.views',
    url(r'^events/?$', 'events', name='events'),
    url(r'^profiles/(?P<username>[^/]+)/?$', 'profile_view',
        name="devmo_profile_view"),
    url(r'^profiles/(?P<username>[^/]+)/roles$', teamwork.views.user_roles),
    url(r'^profiles/(?P<username>[^/]+)/edit$', 'profile_edit',
        name="devmo_profile_edit"),
    url(r'^profile/?$', 'my_profile', name="devmo_my_profile"),
    url(r'^profile/edit/?$', 'my_profile_edit',
        name="devmo_my_profile_edit"),
)
