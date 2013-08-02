from django.conf.urls import patterns, url

urlpatterns = patterns('landing.views',
    url(r'^$', 'home', name='home'),
    url(r'^addons/?$', 'addons', name='addons'),
    url(r'^mozilla/?$', 'mozilla', name='mozilla'),
    url(r'^mobile/?$', 'mobile', name='mobile'),
    url(r'^web/?$', 'web', name='web'),
    url(r'^newsletter/?$', 'apps_newsletter', name='apps_newsletter'),
    url(r'^learn/?$', 'learn', name='learn'),
    url(r'^learn/html/?$', 'learn_html', name='learn_html'),
    url(r'^learn/html5/?$', 'learn_html5', name='learn_html5'),
    url(r'^learn/css/?$', 'learn_css', name='learn_css'),
    url(r'^learn/javascript/?$', 'learn_javascript', name='learn_javascript'),
    url(r'^promote/?$', 'promote_buttons', name='promote'),
    url(r'^promote/buttons/?$', 'promote_buttons', name='promote_buttons'),
    url(r'^forum-archive/?$', 'forum_archive', name='forum_archive'),
    url(r'^waffles.js$', 'waffles', name='waffles'),
)
