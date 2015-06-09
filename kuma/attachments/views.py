import json
import mimetypes

import jinja2
from tower import ugettext as _

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import (Http404,
                         HttpResponse,
                         HttpResponsePermanentRedirect,
                         HttpResponseRedirect)
from django.shortcuts import get_object_or_404, render
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.http import require_GET, require_POST

from constance import config

from kuma.core.decorators import login_required
from kuma.core.utils import paginate
from kuma.wiki.constants import DOCUMENTS_PER_PAGE
from kuma.wiki.models import Document

from .forms import AttachmentRevisionForm
from .models import Attachment
from .utils import attachments_json, convert_to_http_date


# Mime types used on MDN
OVERRIDE_MIMETYPES = {
    'image/jpeg': '.jpeg, .jpg, .jpe',
    'image/vnd.adobe.photoshop': '.psd',
}


def guess_extension(_type):
    return OVERRIDE_MIMETYPES.get(_type, mimetypes.guess_extension(_type))


@require_GET
def list_files(request):
    """Returns listing of all files"""
    files = paginate(request,
                     Attachment.objects.order_by('title'),
                     per_page=DOCUMENTS_PER_PAGE)
    return render(request, 'attachments/list_files.html', {'files': files})


def raw_file(request, attachment_id, filename):
    """Serve up an attachment's file."""
    # TODO: For now this just grabs and serves the file in the most
    # naive way. This likely has performance and security implications.
    qs = Attachment.objects.select_related('current_revision')
    attachment = get_object_or_404(qs, pk=attachment_id)
    if attachment.current_revision is None:
        raise Http404
    if request.get_host() == settings.ATTACHMENT_HOST:
        rev = attachment.current_revision
        resp = HttpResponse(rev.file.read(), content_type=rev.mime_type)
        resp['Last-Modified'] = convert_to_http_date(rev.created)
        resp['Content-Length'] = rev.file.size
        resp['X-Frame-Options'] = 'ALLOW-FROM: %s' % settings.DOMAIN
        return resp
    else:
        return HttpResponsePermanentRedirect(attachment.get_file_url())


def mindtouch_file_redirect(request, file_id, filename):
    """Redirect an old MindTouch file URL to a new kuma file URL."""
    attachment = get_object_or_404(Attachment, mindtouch_attachment_id=file_id)
    return HttpResponsePermanentRedirect(attachment.get_file_url())


def attachment_detail(request, attachment_id):
    """Detail view of an attachment."""
    attachment = get_object_or_404(Attachment, pk=attachment_id)
    preview_content = ''
    current = attachment.current_revision

    if current.mime_type in ['image/png', 'image/jpeg', 'image/jpg', 'image/gif']:
        preview_content = jinja2.Markup('<img src="%s" alt="%s" />') % (attachment.get_file_url(), attachment.title)

    return render(
        request,
        'attachments/attachment_detail.html',
        {'attachment': attachment,
         'preview_content': preview_content,
         'revision': attachment.current_revision})


def attachment_history(request, attachment_id):
    """Detail view of an attachment."""
    # For now this is just attachment_detail with a different
    # template. At some point in the near future, it'd be nice to add
    # a few extra bits, like the ability to set an arbitrary revision
    # to be current.
    attachment = get_object_or_404(Attachment, pk=attachment_id)
    return render(
        request,
        'attachments/attachment_history.html',
        {'attachment': attachment,
         'revision': attachment.current_revision})


@require_POST
@xframe_options_sameorigin
@login_required
def new_attachment(request):
    """Create a new Attachment object and populate its initial
    revision."""

    # No access if no permissions to upload
    if not Attachment.objects.allow_add_attachment_by(request.user):
        raise PermissionDenied

    document = None
    document_id = request.GET.get('document_id', None)
    if document_id:
        try:
            document = Document.objects.get(id=int(document_id))
        except (Document.DoesNotExist, ValueError):
            pass

    form = AttachmentRevisionForm(data=request.POST, files=request.FILES)
    if form.is_valid():
        rev = form.save(commit=False)
        rev.creator = request.user
        attachment = Attachment.objects.create(title=rev.title,
                                               slug=rev.slug)
        rev.attachment = attachment
        rev.save()

        if document is not None:
            attachment.attach(document, request.user,
                              rev.filename())

        if request.POST.get('is_ajax', ''):
            response = render(
                request,
                'attachments/includes/attachment_upload_results.html',
                {'result': json.dumps(attachments_json([attachment]))})
        else:
            return HttpResponseRedirect(attachment.get_absolute_url())
    else:
        if request.POST.get('is_ajax', ''):
            allowed_list = config.WIKI_ATTACHMENT_ALLOWED_TYPES.split()
            allowed_types = ', '.join(map(guess_extension, allowed_list))
            error_obj = {
                'title': request.POST.get('is_ajax', ''),
                'error': _(u'The file provided is not valid. '
                           u'File must be one of these types: %s.') % allowed_types
            }
            response = render(
                request,
                'attachments/includes/attachment_upload_results.html',
                {'result': json.dumps([error_obj])})
        else:
            response = render(
                request,
                'attachments/edit_attachment.html',
                {'form': form})
    return response


@login_required
def edit_attachment(request, attachment_id):

    # No access if no permissions to upload
    if not request.user.has_perm('attachments.change_attachment'):
        raise PermissionDenied

    attachment = get_object_or_404(Attachment,
                                   pk=attachment_id)
    if request.method == 'POST':
        form = AttachmentRevisionForm(data=request.POST, files=request.FILES)
        if form.is_valid():
            rev = form.save(commit=False)
            rev.creator = request.user
            rev.attachment = attachment
            rev.save()
            return HttpResponseRedirect(attachment.get_absolute_url())
    else:
        form = AttachmentRevisionForm()
    return render(request, 'attachments/edit_attachment.html', {'form': form})
