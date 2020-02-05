import calendar
import mimetypes

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponseNotModified, StreamingHttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import parse_http_date_safe
from django.views.decorators.cache import cache_control, never_cache
from django.views.decorators.clickjacking import xframe_options_sameorigin

from kuma.core.decorators import (ensure_wiki_domain, login_required,
                                  shared_cache_control)
from kuma.core.utils import is_untrusted
from kuma.wiki.decorators import process_document_path
from kuma.wiki.models import Document

from .forms import AttachmentRevisionForm
from .models import Attachment
from .utils import allow_add_attachment_by, convert_to_http_date


# Mime types used on MDN
OVERRIDE_MIMETYPES = {
    'image/jpeg': '.jpeg, .jpg, .jpe',
    'image/vnd.adobe.photoshop': '.psd',
}

IMAGE_MIMETYPES = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif']


def guess_extension(_type):
    return OVERRIDE_MIMETYPES.get(_type, mimetypes.guess_extension(_type))


@cache_control(public=True, max_age=60 * 15)
def raw_file(request, attachment_id, filename):
    """
    Serve up an attachment's file.
    """
    qs = Attachment.objects.select_related('current_revision')
    attachment = get_object_or_404(qs, pk=attachment_id)
    rev = attachment.current_revision
    if rev is None:
        raise Http404

    # Attachments must be served from safe (untrusted) domains
    if not is_untrusted(request):
        return redirect(attachment.get_file_url(), permanent=True)

    # NOTE: All of this, just to support conditional requests (last-modified / if-modified-since)
    # Very important while we're potentially serving attachments from disk.
    # Far less important when we're just redirecting to S3.
    # Consider removing?
    if_modified_since = parse_http_date_safe(request.META.get('HTTP_IF_MODIFIED_SINCE'))
    if if_modified_since and if_modified_since >= calendar.timegm(rev.created.utctimetuple()):
        response = HttpResponseNotModified()
        response['Last-Modified'] = convert_to_http_date(rev.created)
        return response

    if settings.ATTACHMENTS_USE_S3:
        response = redirect(rev.file.url)
    else:
        response = StreamingHttpResponse(rev.file, content_type=rev.mime_type)
        response['Content-Length'] = rev.file.size

    response['Last-Modified'] = convert_to_http_date(rev.created)
    response['X-Frame-Options'] = f'ALLOW-FROM {settings.DOMAIN}'
    return response


@shared_cache_control(s_maxage=60 * 60 * 24 * 30)
def mindtouch_file_redirect(request, file_id, filename):
    """Redirect an old MindTouch file URL to a new kuma file URL."""
    attachment = get_object_or_404(Attachment, mindtouch_attachment_id=file_id)
    return redirect(attachment.get_file_url(), permanent=True)


@ensure_wiki_domain
@never_cache
@xframe_options_sameorigin
@login_required
@process_document_path
def edit_attachment(request, document_slug, document_locale):
    """
    Create a new Attachment object and populate its initial
    revision or show a separate form view that allows to fix form submission
    errors.

    Redirects back to the document's editing URL on success.
    """
    document = get_object_or_404(
        Document,
        locale=document_locale,
        slug=document_slug,
    )
    if request.method != 'POST':
        return redirect(document.get_edit_url())

    # No access if no permissions to upload
    if not allow_add_attachment_by(request.user):
        raise PermissionDenied

    form = AttachmentRevisionForm(
        data=request.POST,
        files=request.FILES,
        # Only staff users are allowed to upload SVG files because SVG files
        # can contain embedded inline scripts.
        allow_svg_uploads=request.user.is_staff
    )
    if form.is_valid():
        revision = form.save(commit=False)
        revision.creator = request.user
        attachment = Attachment.objects.create(title=revision.title)
        revision.attachment = attachment
        revision.save()
        # adding the attachment to the document's files (M2M)
        attachment.attach(document, request.user, revision)
        return redirect(document.get_edit_url())
    else:
        context = {
            'form': form,
            'document': document,
        }
        return render(request, 'attachments/edit_attachment.html', context)
