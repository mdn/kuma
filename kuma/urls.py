from decorator_include import decorator_include
from django.conf import settings
from django.contrib import admin
from django.shortcuts import render
from django.urls import include, re_path, reverse_lazy
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
from kuma.payments.urls import lang_urlpatterns as payments_lang_urlpatterns
from kuma.payments.views import send_feedback
from kuma.search.urls import (
    lang_base_urlpatterns as search_lang_base_urlpatterns,
    lang_urlpatterns as search_lang_urlpatterns,
)
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

urlpatterns = [re_path("", include("kuma.health.urls"))]
# The non-locale-based landing URL's
urlpatterns += [re_path("", include("kuma.landing.urls"))]
# The locale-based landing URL's
urlpatterns += i18n_patterns(re_path("", include(landing_lang_urlpatterns)))
urlpatterns += i18n_patterns(
    re_path(
        r"^events",
        # Here the "shared_cache_control" decorator is an optimization. It
        # informs the CDN to cache the redirect for a month, so once this URL
        # has been requested by a client, all other client requests will be
        # redirected by the CDN instead of this Django service.
        shared_cache_control(s_maxage=MONTH)(
            RedirectView.as_view(
                url="https://mozilla.org/contribute/events", permanent=False
            )
        ),
        name="events",
    ),
)

if settings.MAINTENANCE_MODE:
    urlpatterns.append(
        re_path(
            r"^admin/.*",
            never_cache(
                RedirectView.as_view(pattern_name="maintenance_mode", permanent=False)
            ),
        )
    )
else:
    # Django admin:
    urlpatterns += [
        re_path(
            r"^admin/wiki/document/purge/", purge_view, name="wiki.admin_bulk_purge"
        ),
        # We don't worry about decorating the views within django.contrib.admin
        # with "never_cache", since most have already been decorated, and the
        # remaining can be safely cached.
        re_path(r"^admin/", admin.site.urls),
    ]

urlpatterns += i18n_patterns(re_path(r"^search/", include(search_lang_urlpatterns)))
urlpatterns += i18n_patterns(re_path(r"^search", include(search_lang_base_urlpatterns)))
urlpatterns += i18n_patterns(
    re_path(r"^docs.json$", document_as_json, name="wiki.json")
)
urlpatterns += i18n_patterns(re_path(r"^docs/", include(wiki_lang_urlpatterns)))
urlpatterns += [re_path("", include("kuma.attachments.urls"))]
urlpatterns += i18n_patterns(
    re_path(r"dashboards/?$", dashboards_index, name="dashboards.index"),
)
urlpatterns += i18n_patterns(
    re_path(r"^dashboards/", include(dashboards_lang_urlpatterns))
)
urlpatterns += [re_path("users/", include("kuma.users.urls"))]
urlpatterns += i18n_patterns(
    re_path(
        r"^contribute/$",
        RedirectView.as_view(url=reverse_lazy("payments_index")),
        name="redirect-to-payments",
    ),
)

urlpatterns += i18n_patterns(re_path(r"^payments/", include(payments_lang_urlpatterns)))
urlpatterns += i18n_patterns(
    re_path("", decorator_include(never_cache, users_lang_urlpatterns))
)

if settings.MAINTENANCE_MODE:
    urlpatterns += i18n_patterns(
        # Redirect if we try to use the "tidings" unsubscribe.
        re_path(
            r"^unsubscribe/.*",
            ensure_wiki_domain(
                never_cache(
                    RedirectView.as_view(
                        pattern_name="maintenance_mode", permanent=False
                    )
                )
            ),
        )
    )
else:
    urlpatterns += i18n_patterns(
        # The first argument to "decorator_include" can be an iterable
        # of view decorators, which are applied in reverse order.
        re_path(
            r"^", decorator_include((ensure_wiki_domain, never_cache), "tidings.urls")
        ),
    )


urlpatterns += [
    # Services and sundry.
    re_path("^api/", include("kuma.api.urls")),
    re_path("", include("kuma.version.urls")),
    # Serve sitemap files.
    re_path(
        r"^sitemap.xml$", serve_from_media_root, {"path": "sitemap.xml"}, name="sitemap"
    ),
    re_path(r"^(?P<path>sitemaps/.+)$", serve_from_media_root, name="sitemaps"),
    re_path(r"^humans.txt$", core_views.humans_txt, name="humans_txt"),
    re_path(
        r"^miel$",
        shared_cache_control(s_maxage=WEEK)(render),
        {"template_name": "500.html", "status": 500},
        name="users.honeypot",
    ),
    # We use our own views for setting language in cookies. But to just align with django, set it like this.
    re_path(r"^i18n/setlang/", core_views.set_language, name="set-language-cookie"),
    re_path(r"^payments/feedback/?$", send_feedback, name="send_feedback"),
]

if settings.SERVE_LEGACY and settings.LEGACY_ROOT:
    urlpatterns.append(
        re_path(
            r"^(?P<path>(diagrams|presentations|samples)/.+)$",
            shared_cache_control(s_maxage=MONTH)(serve),
            {"document_root": settings.LEGACY_ROOT},
        )
    )

if getattr(settings, "DEBUG_TOOLBAR_INSTALLED", False):
    import debug_toolbar

    urlpatterns.append(
        re_path(r"^__debug__/", decorator_include(never_cache, debug_toolbar.urls)),
    )

# Legacy MindTouch redirects. These go last so that they don't mess
# with local instances' ability to serve media.
urlpatterns += [
    re_path(
        r"^@api/deki/files/(?P<file_id>\d+)/=(?P<filename>.+)$",
        attachment_views.mindtouch_file_redirect,
        name="attachments.mindtouch_file_redirect",
    ),
    re_path(r"^(?P<path>.*)$", mindtouch_to_kuma_redirect),
]
