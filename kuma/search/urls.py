from django.conf.urls import url

from rest_framework.urlpatterns import format_suffix_patterns

from . import views


# this allows using ".json" extensions for the view to force json output
urlpatterns = format_suffix_patterns(
    [url(r'^$', views.search, name='search')])

urlpatterns += [
    url(r'^/xml$',
        views.plugin,
        name='search.plugin'),
    url(r'^/suggestions$',
        views.suggestions,
        name='search.suggestions'),
]
