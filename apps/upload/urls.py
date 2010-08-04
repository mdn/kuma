from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('upload.views',
    url(r'^/image/(?P<model_name>\w+\.\w+)/(?P<object_pk>\d+)$',
        'up_image_async', name='upload.up_image_async'),
    url(r'^/image/delete/(?P<image_id>\d+)$',
        'del_image_async', name='upload.del_image_async'),
)
