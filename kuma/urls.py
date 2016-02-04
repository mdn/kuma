from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.shortcuts import redirect
from django.views.static import serve

from kuma.attachments import views as attachment_views
from kuma.core import views as core_views
from kuma.wiki.admin import purge_view
from kuma.wiki.views.legacy import mindtouch_to_kuma_redirect


admin.autodiscover()

handler403 = core_views.handler403
handler404 = core_views.handler404
handler500 = core_views.handler500

urlpatterns = [
    url('', include('kuma.landing.urls')),
    url(r'^events',
        lambda x: redirect('https://mozilla.org/contribute/events'),
        name='events'),

    # Django admin:
    url(r'^admin/wiki/document/purge/',
        purge_view,
        name='wiki.admin_bulk_purge'),
    url(r'^admin/', include('smuggler.urls')),
    url(r'^admin/', include(admin.site.urls)),

    url(r'^search', include('kuma.search.urls')),

    # Special-case here because this used to live in the wiki app and
    # needs to keep its historical URL.
    url(r'^docs/files$',
        attachment_views.list_files,
        name='attachments.list_files'),
    url(r'^docs', include('kuma.wiki.urls')),

    url(r'^files/', include('kuma.attachments.urls')),
    url(r'^', include('kuma.dashboards.urls')),

    # Users
    url('', include('kuma.users.urls')),


    # Services and sundry.
    url(r'^', include('tidings.urls')),
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
        url(r'^%s/(?P<path>.*)$' % media_url,
            serve,
            {'document_root': settings.MEDIA_ROOT}),
    ]

# Legacy MindTouch redirects. These go last so that they don't mess
# with local instances' ability to serve media.
urlpatterns += [
    url(r'^@api/deki/files/(?P<file_id>\d+)/=(?P<filename>.+)$',
        attachment_views.mindtouch_file_redirect,
        name='attachments.mindtouch_file_redirect'),
    url(r'^(?P<path>.*)$',
        mindtouch_to_kuma_redirect),
]
