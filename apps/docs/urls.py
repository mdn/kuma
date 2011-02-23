from django.conf.urls.defaults import *


urlpatterns = patterns('docs.views',
    url(r'^docs/?$', 'docs', name='docs'),
)
