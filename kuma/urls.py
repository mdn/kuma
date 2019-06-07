from decorator_include import decorator_include
from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.decorators.cache import never_cache
from django.views.generic import RedirectView
from django.views.static import serve

import kuma.views
from kuma.api.v1 import views as api_v1_views
from kuma.attachments import views as attachment_views
from kuma.core import views as core_views
from kuma.core.decorators import shared_cache_control
from kuma.core.urlresolvers import i18n_patterns
from kuma.dashboards.urls import lang_urlpatterns as dashboards_lang_urlpatterns
from kuma.dashboards.views import index as dashboards_index
from kuma.landing.urls import lang_urlpatterns as landing_lang_urlpatterns
from kuma.payments import views as payment_views
from kuma.payments.urls import (
    lang_urlpatterns as payments_lang_urlpatterns)
from kuma.search.urls import (
    lang_base_urlpatterns as search_lang_base_urlpatterns,
    lang_urlpatterns as search_lang_urlpatterns)
from kuma.users.urls import lang_urlpatterns as users_lang_urlpatterns
from kuma.wiki.admin import purge_view
from kuma.wiki.urls import lang_urlpatterns as wiki_lang_urlpatterns
from kuma.wiki.views.document import as_json as document_as_json
from kuma.wiki.views.legacy import mindtouch_to_kuma_redirect


serve_from_media_root = shared_cache_control(kuma.views.serve_from_media_root)

admin.autodiscover()

handler403 = core_views.handler403
handler404 = core_views.handler404
handler500 = core_views.handler500

urlpatterns = [url('', include('kuma.health.urls'))]
urlpatterns += [url('', include('kuma.landing.urls'))]
urlpatterns += i18n_patterns(url('', include(landing_lang_urlpatterns)))
urlpatterns += i18n_patterns(
    url(
        r'^events',
        shared_cache_control(RedirectView.as_view(
            url='https://mozilla.org/contribute/events',
            permanent=False
        )),
        name='events'
    ),
)

if settings.MAINTENANCE_MODE:
    urlpatterns.append(
        url(
            r'^admin/.*',
            never_cache(RedirectView.as_view(
                pattern_name='maintenance_mode',
                permanent=False
            ))
        )
    )
else:
    # Django admin:
    urlpatterns += [
        url(r'^admin/wiki/document/purge/',
            purge_view,
            name='wiki.admin_bulk_purge'),
        # We don't worry about decorating the views within django.contrib.admin
        # with "never_cache", since most have already been decorated, and the
        # remaining can be safely cached.
        url(r'^admin/', admin.site.urls),
    ]

urlpatterns += i18n_patterns(url(r'^search/',
                                 include(search_lang_urlpatterns)))
urlpatterns += i18n_patterns(url(r'^search',
                                 include(search_lang_base_urlpatterns)))
urlpatterns += i18n_patterns(url(r'^docs.json$', document_as_json,
                                 name='wiki.json'))
urlpatterns += i18n_patterns(url(r'^docs/', include(wiki_lang_urlpatterns)))
urlpatterns += [url('', include('kuma.attachments.urls'))]
urlpatterns += i18n_patterns(
    url(r'dashboards/?$', dashboards_index, name='dashboards.index'),
)
urlpatterns += i18n_patterns(url(r'^dashboards/',
                                 include(dashboards_lang_urlpatterns)))
urlpatterns += [url('users/', include('kuma.users.urls'))]
urlpatterns += i18n_patterns(
    url(r'^payments/$',
        payment_views.contribute,
        name='payments'),
)
urlpatterns += i18n_patterns(
    url(r'^contribute/$',
        RedirectView.as_view(url=reverse_lazy('payments')),
        name='redirect-to-payments'),
)
urlpatterns += i18n_patterns(url(r'^payments/',
                                 include(payments_lang_urlpatterns)))
urlpatterns += i18n_patterns(url('',
                                 decorator_include(never_cache,
                                                   users_lang_urlpatterns)))

if settings.MAINTENANCE_MODE:
    urlpatterns += i18n_patterns(
        # Redirect if we try to use the "tidings" unsubscribe.
        url(
            r'^unsubscribe/.*',
            never_cache(RedirectView.as_view(
                pattern_name='maintenance_mode',
                permanent=False
            ))
        )
    )
else:
    urlpatterns += i18n_patterns(
        url(r'^', decorator_include(never_cache, 'tidings.urls')),
    )


urlpatterns += [
    # Services and sundry.
    url('', include('kuma.version.urls')),

    # Serve sitemap files.
    url(r'^sitemap.xml$',
        serve_from_media_root,
        {'path': 'sitemap.xml'},
        name='sitemap'),
    url(r'^(?P<path>sitemaps/.+)$', serve_from_media_root, name='sitemaps'),

    # Serve the humans.txt file.
    url(r'^humans.txt$',
        shared_cache_control(serve),
        {'document_root': settings.HUMANSTXT_ROOT, 'path': 'humans.txt'}),

    url(r'^miel$',
        shared_cache_control(s_maxage=60 * 60 * 24 * 7)(render),
        {'template_name': '500.html', 'status': 500},
        name='users.honeypot'),
    # We use our own views for setting language in cookies. But to just align with django, set it like this.
    url(r'^i18n/setlang/', core_views.set_language, name='set-language-cookie'),
]

# Include API view for signaling feature
urlpatterns += [
    url(r'^api/v1/bc-signal/?$',
        api_v1_views.bc_signal, name='api.v1.bc_signal')
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
            shared_cache_control(s_maxage=60 * 60 * 24 * 30)(serve),
            {'document_root': settings.LEGACY_ROOT}
        )
    )

if getattr(settings, 'DEBUG_TOOLBAR_INSTALLED', False):
    import debug_toolbar
    urlpatterns.append(
        url(r'^__debug__/',
            decorator_include(never_cache, debug_toolbar.urls)),
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
