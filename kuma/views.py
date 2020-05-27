from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.http import require_safe
from django.views.static import serve

from kuma.core.decorators import shared_cache_control
from kuma.wiki.tasks import sitemap_storage


@shared_cache_control(s_maxage=60 * 60)
@require_safe
def serve_sitemap(request, path):
    """
    A convenience view for serving sitemap files.

    NOTE: This will only be used for local development. For the stage
          and production sites, all of the sitemap requests will be
          served from S3 via the CDN.

    TODO: After we're using S3 in both stage and production for the
          sitemap files, settings.SITEMAP_USE_S3 will always be true
          (it could be removed) and this function collapses to just
          that case, and will only be used for local development.
    """
    if settings.SITEMAP_USE_S3:
        with sitemap_storage.open(path, "rb") as sitemap_file:
            return HttpResponse(
                sitemap_file.read(), content_type="application/xml; charset=utf-8"
            )
    return serve(request, path, document_root=settings.MEDIA_ROOT)
