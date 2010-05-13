from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('search.views',
    url(r'^$', 'search', name='search'),
)
