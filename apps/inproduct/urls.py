from django.conf.urls.defaults import patterns, url

from inproduct import views

urlpatterns = patterns('',
    url(r'/(?P<product>[^/]+)/(?P<version>[^/]+)/(?P<platform>[^/]+)/'
        r'(?P<locale>[^/]+)(?:/(?P<topic>[^/]+))?/?',
        views.redirect, name='inproduct.redirect'),
)
