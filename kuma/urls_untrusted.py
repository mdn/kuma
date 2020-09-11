from django.conf import settings
from django.urls import include, re_path

from kuma.core import views as core_views
from kuma.core.urlresolvers import i18n_patterns
from kuma.landing.views import robots_txt
from kuma.wiki.urls_untrusted import lang_urlpatterns as wiki_lang_urlpatterns

handler403 = core_views.handler403
handler404 = core_views.handler404
handler500 = core_views.handler500

urlpatterns = [
    re_path("", include("kuma.attachments.urls")),
    re_path(r"^robots.txt", robots_txt, name="robots_txt"),
]

if getattr(settings, "DEBUG_TOOLBAR_INSTALLED", False):
    import debug_toolbar

    urlpatterns.append(
        re_path(r"^__debug__/", include(debug_toolbar.urls)),
    )

urlpatterns += i18n_patterns(re_path(r"^docs/", include(wiki_lang_urlpatterns)))
