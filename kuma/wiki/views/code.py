from django.conf import settings
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_control
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.http import require_GET

from kuma.attachments.utils import full_attachment_url

from ..decorators import allow_CORS_GET, process_document_path
from ..models import Document


@cache_control(public=True, max_age=31536000)
@require_GET
@allow_CORS_GET
@xframe_options_exempt
@process_document_path
def code_sample(request, document_slug, document_locale, sample_name):
    """
    Extract a code sample from a document and render it as a standalone
    HTML document
    """
    # Restrict rendering of live code samples to domains outside the site domain.
    if settings.DOMAIN in request.get_host():
        return HttpResponseForbidden()

    document = get_object_or_404(Document, slug=document_slug, locale=document_locale)
    data = document.extract.code_sample(sample_name)
    data["document"] = document
    data["sample_name"] = sample_name
    return render(request, "wiki/code_sample.html", data)


@cache_control(public=True, max_age=31536000)
@require_GET
@allow_CORS_GET
@xframe_options_exempt
@process_document_path
def raw_code_sample_file(
    request, document_slug, document_locale, sample_name, attachment_id, filename
):
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
