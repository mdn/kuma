from decorator_include import decorator_include
from django.conf import settings
from django.contrib import admin
from django.urls import include, re_path
from django.views.decorators.cache import never_cache
from django.views.generic import RedirectView

from kuma.attachments import views as attachment_views
from kuma.core import views as core_views
from kuma.core.decorators import shared_cache_control
from kuma.core.urlresolvers import i18n_patterns
from kuma.users.urls import lang_urlpatterns as users_lang_urlpatterns
from kuma.wiki.urls import lang_urlpatterns as wiki_lang_urlpatterns


DAY = 60 * 60 * 24
MONTH = DAY * 30

admin.autodiscover()

urlpatterns = [re_path("", include("kuma.health.urls"))]
# The non-locale-based landing URL's
urlpatterns += [re_path("", include("kuma.landing.urls"))]
urlpatterns += i18n_patterns(
    re_path(
        r"^events",
        # Here the "shared_cache_control" decorator is an optimization. It
        # informs the CDN to cache the redirect for a month, so once this URL
        # has been requested by a client, all other client requests will be
        # redirected by the CDN instead of this Django service.
        shared_cache_control(s_maxage=MONTH)(
            RedirectView.as_view(
                url="https://community.mozilla.org/events/", permanent=False
            )
        ),
        name="events",
    ),
)

if settings.MAINTENANCE_MODE:
    urlpatterns.append(
        re_path(
            r"^admin/.*",
            never_cache(RedirectView.as_view(url="/", permanent=False)),
        )
    )
else:
    # Django admin:
    urlpatterns += [
        # We don't worry about decorating the views within django.contrib.admin
        # with "never_cache", since most have already been decorated, and the
        # remaining can be safely cached.
        re_path(r"^admin/", admin.site.urls),
    ]

urlpatterns += i18n_patterns(re_path(r"^docs/", include(wiki_lang_urlpatterns)))
urlpatterns += [re_path("", include("kuma.attachments.urls"))]
urlpatterns += [re_path("users/", include("kuma.users.urls"))]
urlpatterns += i18n_patterns(
    re_path("", decorator_include(never_cache, users_lang_urlpatterns))
)
urlpatterns += [
    # Services and sundry.
    re_path("^api/", include("kuma.api.urls")),
    re_path("", include("kuma.version.urls")),
    re_path(r"^humans.txt$", core_views.humans_txt, name="humans_txt"),
    # We use our own views for setting language in cookies. But to just align with django, set it like this.
    re_path(r"^i18n/setlang/", core_views.set_language, name="set-language-cookie"),
]

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
]
