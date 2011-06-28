from django.conf.urls.defaults import *


urlpatterns = patterns('devmo.views',
    url(r'^events/?$', 'events', name='events'),
)
