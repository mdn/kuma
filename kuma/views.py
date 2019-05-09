from django.conf import settings
from django.views.decorators.http import require_safe
from django.views.static import serve


@require_safe
def serve_from_media_root(request, path):
    """
    A convenience view for serving files from the media root directory.
    """
    return serve(request, path, document_root=settings.MEDIA_ROOT)
