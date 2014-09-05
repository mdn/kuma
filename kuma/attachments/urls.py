from django.conf.urls import patterns, url

from .views import (attachment_detail, attachment_history,
                    edit_attachment, new_attachment,
                    raw_file)


urlpatterns = patterns('',
   url(r'^new/$',
       new_attachment,
       name='attachments.new_attachment'),
   url(r'^(?P<attachment_id>\d+)/$',
       attachment_detail,
       name='attachments.attachment_detail'),
   url(r'^(?P<attachment_id>\d+)/edit/$',
       edit_attachment,
       name='attachments.edit_attachment'),
   url(r'^(?P<attachment_id>\d+)/history/$',
       attachment_history,
       name='attachments.attachment_history'),
   url(r'^(?P<attachment_id>\d+)/(?P<filename>.+)$',
       raw_file,
       name='attachments.raw_file'),
)
