from django.conf.urls.defaults import *


urlpatterns = patterns('landing.views',
    url(r'^$', 'home', name='home'),
    url(r'^addons/?$', 'addons', name='addons'),
    url(r'^mozilla/?$', 'mozilla', name='mozilla'),
    url(r'^mobile/?$', 'mobile', name='mobile'),
    url(r'^search/?$', 'search', name='search'),
    url(r'^web/?$', 'web', name='web'),
    url(r'^learn/?$', 'learn', name='learn'),
    url(r'^learn/html/?$', 'learn_html', name='learn_html'),
    url(r'^learn/css/?$', 'learn_css', name='learn_css'),
    url(r'^learn/javascript/?$', 'learn_javascript', name='learn_javascript'),
)
