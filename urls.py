from django.conf.urls import include, patterns, url
from django.conf import settings
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.shortcuts import redirect, render
from django.views.i18n import javascript_catalog
from django.views.decorators.cache import cache_page

import badger


admin.autodiscover()
badger.autodiscover()


# Handle 404 and 500 errors
def _error_page(request, status):
    """Render error pages with jinja2."""
    return render(request, '%d.html' % status, status=status)
handler403 = lambda r: _error_page(r, 403)
handler404 = lambda r: _error_page(r, 404)
handler500 = lambda r: _error_page(r, 500)

urlpatterns = patterns('',
   # Home / landing pages:
    ('', include('landing.urls')),
    (r'^demos/', include('kuma.demos.urls')),
    (r'^events/?', include('kuma.events.urls')),
    (r'^demos', lambda x: redirect('demos')),

    # Django admin:
    (r'^grappelli/', include('grappelli.urls')),
    url(r'^admin/wiki/document/purge/',
        'kuma.wiki.admin.purge_view',
        name='wiki.admin_bulk_purge'),
    (r'^admin/', include('smuggler.urls')),
    (r'^admin/', include(admin.site.urls)),

    (r'^search', include('kuma.search.urls')),

    # Special-case here because this used to live in the wiki app and
    # needs to keep its historical URL.
    url(r'^docs/files$',
        'kuma.attachments.views.list_files',
        name='attachments.list_files'),
    (r'^docs', include('kuma.wiki.urls')),

    # Javascript translations.
    url(r'^jsi18n/.*$', cache_page(60 * 60 * 24 * 365)(javascript_catalog),
        {'domain': 'javascript', 'packages': [settings.ROOT_PACKAGE]},
        name='jsi18n'),

    url(r'^files/', include('kuma.attachments.urls')),
    url(r'^', include('kuma.dashboards.urls')),

    # Flagged content.
    url(r'^flagged/$',
        'contentflagging.views.flagged',
        name='contentflagging.flagged'),

    # Users
    ('', include('kuma.users.urls')),

    # Badges
    (r'^badges/', include('badger.urls_simple')),

    # Services and sundry.
    (r'^', include('tidings.urls')),
    (r'^humans.txt$', 'django.views.static.serve',
        {'document_root': settings.HUMANSTXT_ROOT, 'path': 'humans.txt'}),

    url(r'^miel$', handler500, name='users.honeypot'),
)

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()

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
                            'kuma.attachments.views.mindtouch_file_redirect',
                            name='attachments.mindtouch_file_redirect'),
                        (r'^(?P<path>.*)$', 'kuma.wiki.views.mindtouch_to_kuma_redirect'),
)
