from django.conf.urls import patterns, url


urlpatterns = patterns('docs.views',
    url(r'^docs/?$', 'docs', name='docs'),
)
