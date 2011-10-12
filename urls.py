from django.conf.urls.defaults import include, patterns, url
from django.conf import settings
from django.contrib import admin
from django.views.i18n import javascript_catalog
from django.views.decorators.cache import cache_page

import authority
import jingo


admin.autodiscover()
authority.autodiscover()

urlpatterns = patterns('',
   # Home / landing pages:
    ('', include('landing.urls')),
    ('', include('docs.urls')),
    ('', include('devmo.urls')),
    (r'^logout/$', 'dekicompat.views.logout'),
    (r'^demos/', include('demos.urls')),

    # Django admin:
    (r'^admin/', include('smuggler.urls')),
    (r'^admin/', include(admin.site.urls)),

    #(r'^search', include('search.urls')),
    #(r'^forums', include('forums.urls')),
    #(r'^questions', include('questions.urls')),
    #(r'^flagged', include('flagit.urls')),
    #(r'^upload', include('upload.urls')),
    #(r'^kb', include('wiki.urls')),
    #(r'^gallery', include('gallery.urls')),
    #(r'^army-of-awesome', include('customercare.urls')),
    #(r'^chat', include('chat.urls')),
    #(r'^1', include('inproduct.urls')),

    # Kitsune admin (not Django admin).
    #(r'^admin/', include('kadmin.urls')),

    # Javascript translations.
    #url(r'^jsi18n/.*$', cache_page(60 * 60 * 24 * 365)(javascript_catalog),
    #    {'domain': 'javascript', 'packages': ['kitsune']}, name='jsi18n'),

    #url(r'^', include('dashboards.urls')),

    # Users
    ('', include('users.urls')),

    # Services and sundry.
    #(r'', include('sumo.urls')),
    (r'^humans.txt$', 'django.views.static.serve',
        {'document_root': settings.HUMANSTXT_ROOT, 'path': 'humans.txt'}),
)

# Handle 404 and 500 errors
def _error_page(request, status):
    """Render error pages with jinja2."""
    return jingo.render(request, '%d.html' % status, status=status)
handler404 = lambda r: _error_page(r, 404)
handler500 = lambda r: _error_page(r, 500)

if settings.SERVE_MEDIA:
    media_url = settings.MEDIA_URL.lstrip('/').rstrip('/')
    urlpatterns += patterns('',
        (r'^%s/(?P<path>.*)$' % media_url, 'django.views.static.serve',
          {'document_root': settings.MEDIA_ROOT}),
    )
