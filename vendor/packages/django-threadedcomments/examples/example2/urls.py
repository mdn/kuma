from django.conf.urls.defaults import patterns, url, include
from voting.views import xmlhttprequest_vote_on_object
from threadedcomments.models import ThreadedComment
from django.conf import settings

urlpatterns = patterns('',
    url(r'^register/$', 'exampleblog.views.register', name="exampleblog_register"),
    url(r'^login/$', 'exampleblog.views.auth_login', name="exampleblog_login"),
    url(r'^check_exists/$', 'exampleblog.views.check_exists', name="exampleblog_checkexists"),
    url(r'^blog/$', 'exampleblog.views.latest_post', name="exampleblog_latest"),
    url(r'^vote/(?P<object_id>\d+)/(?P<direction>up|down|clear)vote/$', xmlhttprequest_vote_on_object, { 'model' : ThreadedComment }, name="vote_on_object"),
    url(r'^partial/(?P<comment_id>\d+)/$', 'exampleblog.views.comment_partial', name="comment_partial"),
    (r'^threadedcomments/', include('threadedcomments.urls')),
    (r'^admin/', include('django.contrib.admin.urls')),
    (r'^site_media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
)
