from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^new/$',
        views.new_attachment,
        name='attachments.new_attachment'),
    url(r'^(?P<attachment_id>\d+)/$',
        views.attachment_detail,
        name='attachments.attachment_detail'),
    url(r'^(?P<attachment_id>\d+)/edit/$',
        views.edit_attachment,
        name='attachments.edit_attachment'),
    url(r'^(?P<attachment_id>\d+)/history/$',
        views.attachment_history,
        name='attachments.attachment_history'),
    url(r'^(?P<attachment_id>\d+)/(?P<filename>.+)$',
        views.raw_file,
        name='attachments.raw_file'),
]
