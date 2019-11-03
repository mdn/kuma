

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_control
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.http import require_GET

from kuma.attachments.utils import full_attachment_url

from ..decorators import allow_CORS_GET, process_document_path
from ..jobs import DocumentCodeSampleJob
from ..models import Document


@cache_control(public=True, max_age=60 * 60 * 24)
@require_GET
@allow_CORS_GET
@xframe_options_exempt
@process_document_path
def code_sample(request, document_slug, document_locale, sample_name):
    """
    Extract a code sample from a document and render it as a standalone
    HTML document
    """
    # Restrict rendering of live code samples to specified hosts
    if request.get_host() not in (settings.ATTACHMENT_HOST,
                                  settings.ATTACHMENT_ORIGIN):
        raise PermissionDenied

    document = get_object_or_404(Document, slug=document_slug,
                                 locale=document_locale)
    job = DocumentCodeSampleJob(generation_args=[document.pk])
    data = job.get(document.pk, sample_name)
    data['document'] = document
    data['sample_name'] = sample_name
    return render(request, 'wiki/code_sample.html', data)


@cache_control(public=True, max_age=60 * 60 * 24 * 5)
@require_GET
@allow_CORS_GET
@xframe_options_exempt
@process_document_path
def raw_code_sample_file(request, document_slug, document_locale,
                         sample_name, attachment_id, filename):
    """
    A view redirecting to the real file serving view of the attachments app.
    This exists so the writers can use relative paths to files in the
    code samples instead of hard coding he file serving URLs.

    For example on a code sample with the URL:

    https://mdn.mozillademos.org/fr/docs/Web/CSS/Tools/Outil_Selecteur_Couleurs_CSS$samples/ColorPIcker_Tool

    This would allow having files referred to in the CSS as::

       url("files/6067/canvas-controls.png")

    """
    return redirect(full_attachment_url(attachment_id, filename))
