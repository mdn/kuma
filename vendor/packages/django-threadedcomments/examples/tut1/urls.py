from django.conf.urls.defaults import patterns, include

urlpatterns = patterns('',
     (r'^blog/$', 'blog.views.latest_post'),
     (r'^admin/', include('django.contrib.admin.urls')),
     (r'^threadedcomments/', include('threadedcomments.urls')),
)
