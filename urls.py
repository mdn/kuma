from django.conf.urls.defaults import include, patterns, url
from django.conf import settings
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.shortcuts import redirect
from django.views.i18n import javascript_catalog
from django.views.decorators.cache import cache_page

import authority
import jingo


admin.autodiscover()
authority.autodiscover()

urlpatterns = patterns('',
   # Home / landing pages:
    ('', include('landing.urls')),
    ('', include('devmo.urls')),
    (r'^logout/$', 'dekicompat.views.logout'),
    (r'^demos/', include('demos.urls')),
    (r'^demos', lambda x: redirect('demos.views.home')),

    # Django admin:
    (r'^admin/', include('smuggler.urls')),
    (r'^admin/', include(admin.site.urls)),

    (r'^search', include('search.urls')),
    #(r'^forums', include('forums.urls')),
    #(r'^questions', include('questions.urls')),
    #(r'^flagged', include('flagit.urls')),
    #(r'^upload', include('upload.urls')),

    # Docs landing page and next-gen kuma wiki
    ('', include('docs.urls')),
    (r'^docs', include('wiki.urls')),

    #(r'^gallery', include('gallery.urls')),
    #(r'^army-of-awesome', include('customercare.urls')),
    #(r'^chat', include('chat.urls')),
    #(r'^1', include('inproduct.urls')),

    # Kitsune admin (not Django admin).
    #(r'^admin/', include('kadmin.urls')),

    # Javascript translations.
    url(r'^jsi18n/.*$', cache_page(60 * 60 * 24 * 365)(javascript_catalog),
        {'domain': 'javascript', 'packages': [settings.ROOT_PACKAGE]},
        name='jsi18n'),

    url(r'^', include('dashboards.urls')),

    # Files.
    url(r'^files/new/$',
        'wiki.views.new_attachment',
        name='wiki.new_attachment'),
    url(r'^files/(?P<attachment_id>\d+)/$',
        'wiki.views.attachment_detail',
        name='wiki.attachment_detail'),
    url(r'^files/(?P<attachment_id>\d+)/edit/$',
        'wiki.views.edit_attachment',
        name='wiki.edit_attachment'),
    url(r'^files/(?P<attachment_id>\d+)/history/$',
        'wiki.views.attachment_history',
        name='wiki.attachment_history'),
    url(r'^files/(?P<attachment_id>\d+)/(?P<filename>.+)$',
        'wiki.views.raw_file',
        name='wiki.raw_file'),

    # Users
    ('', include('users.urls')),

    # Auth keys
    (r'^keys/', include('authkeys.urls')),

    # Services and sundry.
    #(r'', include('sumo.urls')),
    (r'^humans.txt$', 'django.views.static.serve',
        {'document_root': settings.HUMANSTXT_ROOT, 'path': 'humans.txt'}),
)

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()

# Handle 404 and 500 errors
def _error_page(request, status):
    """Render error pages with jinja2."""
    return jingo.render(request, '%d.html' % status, status=status)
handler403 = lambda r: _error_page(r, 403)
handler404 = lambda r: _error_page(r, 404)
handler500 = lambda r: _error_page(r, 500)

if settings.SERVE_MEDIA:
    media_url = settings.MEDIA_URL.lstrip('/').rstrip('/')
    urlpatterns += patterns('',
        (r'^%s/(?P<path>.*)$' % media_url, 'django.views.static.serve',
          {'document_root': settings.MEDIA_ROOT}),
    )

# Legacy MindTouch redirects. These go last so that they don't mess
# with local instances' ability to serve media.
urlpatterns += patterns('',
                        url(r'^@api/deki/files/(?P<file_id>\d+)/=(?P<filename>.+)$',
                            'wiki.views.mindtouch_file_redirect',
                            name='wiki.mindtouch_file_redirect'),
                        (r'^(?P<path>.*)$', 'wiki.views.mindtouch_to_kuma_redirect'),
)
