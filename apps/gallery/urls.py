from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('gallery.views',
    url(r'^$', 'gallery', name='gallery.gallery'),
    url(r'^/async$', 'gallery_async', name='gallery.async'),
    url(r'^/(?P<media_type>\w+)s$', 'gallery', name='gallery.gallery_media'),
    url(r'^/(?P<media_type>\w+)s/search$', 'search', name='gallery.search'),
    url(r'^/(?P<media_type>\w+)/upload_async$', 'up_media_async',
        name='gallery.up_media_async'),
    url(r'^/(?P<media_type>\w+)/(?P<media_id>\d+)/delete_async$',
        'del_media_async', name='gallery.del_media_async'),
    url(r'^/(?P<media_type>\w+)/(?P<media_id>\d+)$',
        'media', name='gallery.media'),
)
