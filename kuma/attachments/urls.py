from django.conf.urls import url

from . import views


urlpatterns = [
    url(
        r"^files/(?P<attachment_id>\d+)/(?P<filename>.+)$",
        views.raw_file,
        name="attachments.raw_file",
    ),
    url(
        r"^@api/deki/files/(?P<file_id>\d+)/=(?P<filename>.+)$",
        views.mindtouch_file_redirect,
        name="attachments.mindtouch_file_redirect",
    ),
]
