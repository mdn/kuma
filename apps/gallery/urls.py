from django.conf.urls.defaults import patterns, url
from django.views.generic.base import RedirectView

urlpatterns = patterns('gallery.views',
    url(r'^/$', RedirectView.as_view(url='images'), name='gallery.home'),
    url(r'^/async$', 'gallery_async', name='gallery.async'),
    url(r'^/(?P<media_type>\w+)s$', 'gallery', name='gallery.gallery'),
    url(r'^/(?P<media_type>\w+)s/search$', 'search', name='gallery.search'),
    url(r'^/(?P<media_type>\w+)s/upload$', 'upload', name='gallery.upload'),
    url(r'^/(?P<media_type>\w+)s/cancel_draft$', 'cancel_draft',
        name='gallery.cancel_draft'),
    url(r'^/(?P<media_type>\w+)/upload_async$', 'upload_async',
        name='gallery.upload_async'),
    url(r'^/(?P<media_type>\w+)/(?P<media_id>\d+)/delete$', 'delete_media',
        name='gallery.delete_media'),
    url(r'^/(?P<media_type>\w+)/(?P<media_id>\d+)/edit$', 'edit_media',
        name='gallery.edit_media'),
    url(r'^/(?P<media_type>\w+)/(?P<media_id>\d+)$', 'media',
        name='gallery.media'),
)
