from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^doc/(?P<locale>[^/]+)/(?P<slug>.*)$',
        views.doc,
        name='api.v1.doc'),
    url(r'^whoami/?$',
        views.whoami,
        name='api.v1.whoami'),
    url(r'^search/(?P<locale>[^/]+)/?$',
        views.search,
        name='api.v1.search'),
]
