from django.conf.urls.defaults import *

urlpatterns = patterns('forums.views',
    url(r'^$', 'forums', name='forums.forums'),
    url(r'^(?P<forum>\w+)$', 'threads', name='forums.threads'),
    url(r'^(?P<forum>\w+)/(?P<thread>\d+)$', 'posts', name='forums.posts'),
)
