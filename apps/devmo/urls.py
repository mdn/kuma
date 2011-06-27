from django.conf.urls.defaults import *


urlpatterns = patterns('devmo.views',
    url(r'^calendar/?$', 'calendar', name='devmo.calendar'),
)
