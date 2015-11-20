# -*- coding: utf-8 -*-
import re

from constance import config
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.http import require_GET

from kuma.attachments.utils import full_attachment_url

from ..decorators import allow_CORS_GET, process_document_path
from ..models import Document


@require_GET
@allow_CORS_GET
@xframe_options_exempt
@process_document_path
def code_sample(request, document_slug, document_locale, sample_id):
    """
    Extract a code sample from a document and render it as a standalone
    HTML document
    """
    # Restrict rendering of live code samples to specified hosts
    if not re.search(config.KUMA_WIKI_IFRAME_ALLOWED_HOSTS,
                     request.build_absolute_uri()):
        raise PermissionDenied

    document = get_object_or_404(Document, slug=document_slug,
                                 locale=document_locale)
    data = document.extract_code_sample(sample_id)
    data['document'] = document
    return render(request, 'wiki/code_sample.html', data)


@require_GET
@allow_CORS_GET
@xframe_options_exempt
@process_document_path
def raw_code_sample_file(request, document_slug, document_locale,
                         sample_id, attachment_id, filename):
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
