from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('customercare.views',
    url(r'^$', 'landing', name='customercare.landing'),
)
