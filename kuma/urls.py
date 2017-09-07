from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.views.static import serve
from django.views.generic import RedirectView
from django.views.decorators.http import require_safe

from kuma.attachments import views as attachment_views
from kuma.core import views as core_views
from kuma.wiki.admin import purge_view
from kuma.wiki.views.legacy import mindtouch_to_kuma_redirect


@require_safe
def serve_from_media_root(request, path):
    """
    A convenience function which also makes it easy to override the
    settings within tests.
    """
    return serve(request, path, document_root=settings.MEDIA_ROOT)


admin.autodiscover()

handler403 = core_views.handler403
handler404 = core_views.handler404
handler500 = core_views.handler500

urlpatterns = [
    url('', include('kuma.health.urls')),
    url('', include('kuma.landing.urls')),
    url(
        r'^events',
        RedirectView.as_view(
            url='https://mozilla.org/contribute/events',
            permanent=False
        ),
        name='events'
    ),
]

if settings.MAINTENANCE_MODE:
    urlpatterns.append(
        url(
            r'^admin/.*',
            RedirectView.as_view(
                pattern_name='maintenance_mode',
                permanent=False
            )
        )
    )
else:
    urlpatterns += [
        # Django admin:
        url(r'^admin/wiki/document/purge/',
            purge_view,
            name='wiki.admin_bulk_purge'),
        url(r'^admin/', include(admin.site.urls)),
    ]

urlpatterns += [
    url(r'^search', include('kuma.search.urls')),
    url(r'^docs', include('kuma.wiki.urls')),
    url('', include('kuma.attachments.urls')),
    url('', include('kuma.dashboards.urls')),
    url('', include('kuma.users.urls')),
]

if settings.MAINTENANCE_MODE:
    urlpatterns.append(
        # Redirect if we try to use the "tidings" unsubscribe.
        url(
            r'^unsubscribe/.*',
            RedirectView.as_view(
                pattern_name='maintenance_mode',
                permanent=False
            )
        )
    )
else:
    urlpatterns.append(
        url(r'^', include('tidings.urls')),
    )


urlpatterns += [
    # Services and sundry.
    url('', include('kuma.version.urls')),

    # Serve sitemap files for AWS (these are never hit in SCL3).
    url(r'^sitemap.xml$',
        serve_from_media_root,
        {'path': 'sitemap.xml'},
        name='sitemap'),
    url(r'^(?P<path>sitemaps/.+)$', serve_from_media_root, name='sitemaps'),

    # Serve the humans.txt file.
    url(r'^humans.txt$',
        serve,
        {'document_root': settings.HUMANSTXT_ROOT, 'path': 'humans.txt'}),

    url(r'^miel$',
        handler500,
        name='users.honeypot'),
]

if settings.SERVE_MEDIA:
    media_url = settings.MEDIA_URL.lstrip('/').rstrip('/')
    urlpatterns += [
        url(r'^%s/(?P<path>.*)$' % media_url, serve_from_media_root),
    ]

if settings.SERVE_LEGACY and settings.LEGACY_ROOT:
    urlpatterns.append(
        url(
            r'^(?P<path>(diagrams|presentations|samples)/.+)$',
            serve,
            {'document_root': settings.LEGACY_ROOT}
        )
    )

if getattr(settings, 'DEBUG_TOOLBAR_INSTALLED', False):
    import debug_toolbar
    urlpatterns.append(
        url(r'^__debug__/', include(debug_toolbar.urls)),
    )

# Legacy MindTouch redirects. These go last so that they don't mess
# with local instances' ability to serve media.
urlpatterns += [
    url(r'^@api/deki/files/(?P<file_id>\d+)/=(?P<filename>.+)$',
        attachment_views.mindtouch_file_redirect,
        name='attachments.mindtouch_file_redirect'),
    url(r'^(?P<path>.*)$',
        mindtouch_to_kuma_redirect),
]
