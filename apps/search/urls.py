from django.conf.urls.defaults import patterns, url


urlpatterns = patterns('search.views',
    url(r'^$', 'search', name='search'),
    url(r'^/xml$', 'plugin', name='search.plugin'),
    url(r'^/suggestions$', 'suggestions', name='search.suggestions'),
    url(r'^/raw$', 'raw', name='search.raw'),
    url(r'^/raw.json$', 'raw', name='search.raw_json', kwargs={"format": "json"}),
)
