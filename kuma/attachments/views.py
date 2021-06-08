import calendar

from django.conf import settings
from django.http import Http404, HttpResponseNotModified, StreamingHttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils.http import parse_http_date_safe
from django.views.decorators.cache import cache_control

from kuma.core.decorators import shared_cache_control

from .models import Attachment
from .utils import convert_to_http_date


@cache_control(public=True, max_age=settings.ATTACHMENTS_CACHE_CONTROL_MAX_AGE)
def raw_file(request, attachment_id, filename):
    """
    Serve up an attachment's file.
    """
    qs = Attachment.objects.select_related("current_revision")
    attachment = get_object_or_404(qs, pk=attachment_id)
    rev = attachment.current_revision
    if rev is None:
        raise Http404

    # Attachments must be served from domains outside the site domain.
    if settings.DOMAIN in request.get_host():
        return redirect(attachment.get_file_url(), permanent=True)

    # NOTE: All of this, just to support conditional requests (last-modified / if-modified-since)
    # Very important while we're potentially serving attachments from disk.
    # Far less important when we're just redirecting to S3.
    # Consider removing?
    if_modified_since = parse_http_date_safe(request.META.get("HTTP_IF_MODIFIED_SINCE"))
    if if_modified_since and if_modified_since >= calendar.timegm(
        rev.created.utctimetuple()
    ):
        response = HttpResponseNotModified()
        response["Last-Modified"] = convert_to_http_date(rev.created)
        return response

    if settings.ATTACHMENTS_USE_S3:
        response = redirect(rev.file.url)
    else:
        response = StreamingHttpResponse(rev.file, content_type=rev.mime_type)
        response["Content-Length"] = rev.file.size

    response["Last-Modified"] = convert_to_http_date(rev.created)
    response["X-Frame-Options"] = f"ALLOW-FROM {settings.DOMAIN}"
    return response


@shared_cache_control(s_maxage=60 * 60 * 24 * 30)
def mindtouch_file_redirect(request, file_id, filename):
    """Redirect an old MindTouch file URL to a new kuma file URL."""
    attachment = get_object_or_404(Attachment, mindtouch_attachment_id=file_id)
    return redirect(attachment.get_file_url(), permanent=True)
