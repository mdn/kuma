from django.conf.urls.defaults import *

urlpatterns = patterns('search.views',
    url(r'^$', 'search', name='search'),
)
