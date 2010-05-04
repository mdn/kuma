from django.conf.urls.defaults import *

urlpatterns = patterns('forums.views',
    url(r'^$', 'forums', name='forums.forums'),
    url(r'^/(?P<forum_slug>[\w\-]+)$', 'threads', name='forums.threads'),
    url(r'^/(?P<forum_slug>[\w\-]+)/new$', 'new_thread',
        name='forums.new_thread'),
    url(r'^/(?P<forum_slug>[\w\-]+)/(?P<thread_id>\d+)$',
        'posts', name='forums.posts'),
    url(r'^/(?P<forum_slug>[\w\-]+)/(?P<thread_id>\d+)/reply$', 'reply', name='forums.reply'),
)
