from django.conf.urls.defaults import patterns, url
from rest_framework.urlpatterns import format_suffix_patterns

# this allows using ".json" extensions for the view to force json output
urlpatterns = format_suffix_patterns(patterns('search.views',
    url(r'^$', 'search', name='search'),
))

urlpatterns += patterns('search.views',
    url(r'^/xml$', 'plugin', name='search.plugin'),
    url(r'^/suggestions$', 'suggestions', name='search.suggestions'),
)
