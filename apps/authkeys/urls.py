from django.conf.urls import patterns, url

urlpatterns = patterns('authkeys.views',
    url(r'^$', 'list', name='authkeys.list'),
    url(r'^/new$', 'new', name='authkeys.new'),
    url(r'^/(?P<pk>\d+)/history$', 'history', name='authkeys.history'),
    url(r'^/(?P<pk>\d+)/delete$', 'delete', name='authkeys.delete'),
)
