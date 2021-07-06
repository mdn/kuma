from django.conf import settings
from django.http import HttpResponseForbidden
from django.http.response import HttpResponse
from django.shortcuts import redirect
from django.views.decorators.cache import cache_control
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.http import require_GET

from kuma.attachments.utils import full_attachment_url

from ..decorators import allow_CORS_GET


@cache_control(public=True, max_age=31536000)
@require_GET
@allow_CORS_GET
@xframe_options_exempt
def code_sample(request, document_path, sample_name):
    """
    Extract a code sample from a document and render it as a standalone
    HTML document
    """
    # Restrict rendering of live code samples to domains outside the site domain.
    if settings.DOMAIN in request.get_host():
        return HttpResponseForbidden()

    return HttpResponse(
        "Legacy ($samples) URLs for live samples are now fully "
        "deprecated and will not work. If you have a document that relies "
        "on a URL with '$samples' in it, switch to using the EmbedLiveSample() "
        "macro instead.\n",
        content_type="text/plain",
    )


@cache_control(public=True, max_age=31536000)
@require_GET
@allow_CORS_GET
@xframe_options_exempt
def raw_code_sample_file(request, document_path, sample_name, attachment_id, filename):
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
