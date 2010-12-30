from django.conf.urls.defaults import patterns, url

from sumo import views


urlpatterns = patterns('',
    url(r'^robots.txt$', views.robots, name='robots.txt'),
)
