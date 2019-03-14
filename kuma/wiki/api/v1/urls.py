from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^doc/(?P<locale>[^/]+)/(?P<slug>.*)$',
        views.doc,
        name='wiki.api.doc'),
]
