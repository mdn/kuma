from django.conf.urls.defaults import include, patterns
from django.conf import settings
from django.contrib import admin

import authority


admin.autodiscover()
authority.autodiscover()

urlpatterns = patterns('',
    (r'^search', include('search.urls')),
    (r'^forums', include('forums.urls')),
    (r'^questions', include('questions.urls')),
    (r'^notifications', include('notifications.urls')),

    # Kitsune admin (not Django admin).
    (r'^admin/', include('kadmin.urls')),
)

# Handle 404 and 500 errors
handler404 = 'sumo.views.handle404'
handler500 = 'sumo.views.handle500'

if settings.DEBUG:
    media_url = settings.MEDIA_URL.lstrip('/').rstrip('/')
    urlpatterns += patterns('',
        (r'^%s/(?P<path>.*)$' % media_url, 'django.views.static.serve',
          {'document_root': settings.MEDIA_ROOT}),
    )
