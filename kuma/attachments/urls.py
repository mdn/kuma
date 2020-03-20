from django.urls import re_path

from . import views


urlpatterns = [
    re_path(
        r"^files/(?P<attachment_id>\d+)/(?P<filename>.+)$",
        views.raw_file,
        name="attachments.raw_file",
    ),
    re_path(
        r"^@api/deki/files/(?P<file_id>\d+)/=(?P<filename>.+)$",
        views.mindtouch_file_redirect,
        name="attachments.mindtouch_file_redirect",
    ),
]
