from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$',
        views.list,
        name='authkeys.list'),
    url(r'^/new$',
        views.new,
        name='authkeys.new'),
    url(r'^/(?P<pk>\d+)/history$',
        views.history,
        name='authkeys.history'),
    url(r'^/(?P<pk>\d+)/delete$',
        views.delete,
        name='authkeys.delete'),
]
