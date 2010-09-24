from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('customercare.views',
    url(r'/twitter_auth', 'twitter_auth', name="customercare.twitter_auth"),
    url(r'', 'landing', name='customercare.landing'),
)
