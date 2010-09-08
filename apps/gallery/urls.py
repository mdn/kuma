from django.conf.urls.defaults import patterns, url


urlpatterns = patterns('gallery.views',
    url(r'^$', 'gallery', name='gallery.gallery'),
    url(r'^/images$', 'gallery', {'filter': 'images'},
        name='gallery.gallery_images'),
    url(r'^/videos$', 'gallery', {'filter': 'videos'},
        name='gallery.gallery_videos'),
    url(r'^/media/(?P<media_type>\w+)/(?P<media_id>\d+)$',
        'media', name='gallery.media'),
)
