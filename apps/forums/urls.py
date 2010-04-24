from django.conf.urls.defaults import *

urlpatterns = patterns('forums.views',
    url(r'^$', 'forums', name='forums.forums'),
    url(r'^/new$', 'new_thread', 'forums.new_thread'),
    url(r'^/reply$', 'reply', name='forums.reply'),
    url(r'^/(?P<forum_slug>[\w\-]+)/(?P<thread_id>\d+)$',
        'posts', name='forums.posts'),
    url(r'^/(?P<forum_slug>[\w\-]+)$', 'threads', name='forums.threads'),
)
