from decorator_include import decorator_include
from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.decorators.cache import never_cache
from django.views.generic import RedirectView
from django.views.static import serve

from kuma.attachments import views as attachment_views
from kuma.core import views as core_views
from kuma.core.decorators import ensure_wiki_domain, shared_cache_control
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
from kuma.views import serve_from_media_root
from kuma.wiki.admin import purge_view
from kuma.wiki.urls import lang_urlpatterns as wiki_lang_urlpatterns
from kuma.wiki.views.document import as_json as document_as_json
from kuma.wiki.views.legacy import mindtouch_to_kuma_redirect


DAY = 60 * 60 * 24
WEEK = DAY * 7
MONTH = DAY * 30

admin.autodiscover()

handler403 = core_views.handler403
handler404 = core_views.handler404
handler500 = core_views.handler500

urlpatterns = [url('', include('kuma.health.urls'))]
# The non-locale-based landing URL's
urlpatterns += [url('', include('kuma.landing.urls'))]
# The locale-based landing URL's
urlpatterns += i18n_patterns(url('', include(landing_lang_urlpatterns)))
urlpatterns += i18n_patterns(
    url(
        r'^events',
        shared_cache_control(s_maxage=MONTH)(RedirectView.as_view(
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
        ensure_wiki_domain(RedirectView.as_view(url=reverse_lazy('payments'))),
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
            ensure_wiki_domain(never_cache(RedirectView.as_view(
                pattern_name='maintenance_mode',
                permanent=False
            )))
        )
    )
else:
    urlpatterns += i18n_patterns(
        # The first argument to "decorator_include" can be an iterable
        # of view decorators, which are applied in reverse order.
        url(r'^', decorator_include((ensure_wiki_domain, never_cache),
                                    'tidings.urls')),
    )


urlpatterns += [
    # Services and sundry.
    url('^api/', include('kuma.api.urls')),
    url('', include('kuma.version.urls')),

    # Serve sitemap files.
    url(r'^sitemap.xml$',
        serve_from_media_root,
        {'path': 'sitemap.xml'},
        name='sitemap'),
    url(r'^(?P<path>sitemaps/.+)$', serve_from_media_root, name='sitemaps'),

    # Serve the humans.txt file.
    url(r'^humans.txt$',
        shared_cache_control(s_maxage=DAY)(serve),
        {'document_root': settings.HUMANSTXT_ROOT, 'path': 'humans.txt'}),

    url(r'^miel$',
        shared_cache_control(s_maxage=WEEK)(render),
        {'template_name': '500.html', 'status': 500},
        name='users.honeypot'),
    # We use our own views for setting language in cookies. But to just align with django, set it like this.
    url(r'^i18n/setlang/', core_views.set_language, name='set-language-cookie'),
]

if settings.SERVE_LEGACY and settings.LEGACY_ROOT:
    urlpatterns.append(
        url(
            r'^(?P<path>(diagrams|presentations|samples)/.+)$',
            shared_cache_control(s_maxage=MONTH)(serve),
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
