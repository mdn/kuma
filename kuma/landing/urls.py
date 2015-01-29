from django.conf.urls import patterns, url

urlpatterns = patterns('kuma.landing.views',
    url(r'^$', 'home', name='home'),
    url(r'^promote/?$', 'promote_buttons', name='promote'),
    url(r'^promote/buttons/?$', 'promote_buttons', name='promote_buttons'),
    url(r'^contribute\.json$', 'contribute_json', name='contribute_json'),
)
