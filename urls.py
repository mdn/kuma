from django.conf.urls.defaults import include, patterns, url
from django.conf import settings
from django.contrib import admin
from django.views.i18n import javascript_catalog
from django.views.decorators.cache import cache_page

import authority


admin.autodiscover()
authority.autodiscover()

urlpatterns = patterns('',
    (r'^search', include('search.urls')),
    (r'^forums', include('forums.urls')),
    (r'^questions', include('questions.urls')),
    (r'^notifications', include('notifications.urls')),
    (r'^flagged', include('flagit.urls')),
    (r'^upload', include('upload.urls')),
    (r'^kb', include('wiki.urls')),
    (r'^gallery', include('gallery.urls')),
    (r'^customercare', include('customercare.urls')),

    # Kitsune admin (not Django admin).
    (r'^admin/', include('kadmin.urls')),

    # Javascript translations.
    url('^jsi18n/.*$', cache_page(60 * 60 * 24 * 365)(javascript_catalog),
        {'domain': 'javascript', 'packages': ['kitsune']}, name='jsi18n'),
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
