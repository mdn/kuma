from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('customercare.views',
    url(r'/twitter_post', 'twitter_post', name="customercare.twitter_post"),
    url(r'', 'landing', name='customercare.landing'),
)
