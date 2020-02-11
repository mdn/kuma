import json

import newrelic.agent
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import (
    Http404,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import etag, require_GET, require_POST
from ratelimit.decorators import ratelimit
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import api_view, authentication_classes

from kuma.core.decorators import (
    block_user_agents,
    ensure_wiki_domain,
    login_required,
    shared_cache_control,
)
from kuma.core.utils import smart_int

from .. import kumascript
from ..decorators import prevent_indexing, process_document_path
from ..events import EditDocumentEvent
from ..models import Document, Revision
from ..templatetags.jinja_helpers import format_comment


@ensure_wiki_domain
@newrelic.agent.function_trace()
@shared_cache_control
@block_user_agents
@prevent_indexing
@process_document_path
@ratelimit(key="user_or_ip", rate="15/m", block=True)
def revision(request, document_slug, document_locale, revision_id):
    """
    View a wiki document revision.
    """
    rev = get_object_or_404(
        Revision.objects.select_related("document"),
        pk=revision_id,
        document__slug=document_slug,
    )
    context = {
        "document": rev.document,
        "revision": rev,
        "comment": format_comment(rev),
    }
    return render(request, "wiki/revision.html", context)


@ensure_wiki_domain
@never_cache
@login_required
@require_POST
def preview(request):
    """
    Create an HTML fragment preview of the posted wiki syntax.
    """
    kumascript_errors = []
    doc = None
    render_preview = True

    wiki_content = request.POST.get("content", "")
    doc_id = request.POST.get("doc_id")
    if doc_id:
        doc = Document.objects.get(id=doc_id)

    if doc and doc.defer_rendering:
        render_preview = False
    else:
        render_preview = kumascript.should_use_rendered(
            doc, request.GET, html=wiki_content
        )
    if render_preview:
        wiki_content, kumascript_errors = kumascript.post(
            request, wiki_content, request.LANGUAGE_CODE
        )
    # TODO: Get doc ID from JSON.
    context = {
        "content": wiki_content,
        "title": request.POST.get("title", ""),
        "kumascript_errors": kumascript_errors,
        "macro_sources": (
            kumascript.macro_sources(force_lowercase_keys=True)
            if kumascript_errors
            else None
        ),
    }
    return render(request, "wiki/preview.html", context)


@ensure_wiki_domain
@shared_cache_control
@block_user_agents
@require_GET
@xframe_options_sameorigin
@process_document_path
@prevent_indexing
@ratelimit(key="user_or_ip", rate="15/m", block=True)
def compare(request, document_slug, document_locale):
    """
    Compare two wiki document revisions.

    The ids are passed as query string parameters (to and from).
    """
    locale = request.GET.get("locale", document_locale)
    if "from" not in request.GET or "to" not in request.GET:
        raise Http404

    doc = get_object_or_404(Document, locale=locale, slug=document_slug)

    from_id = smart_int(request.GET.get("from"))
    to_id = smart_int(request.GET.get("to"))

    revisions = Revision.objects.prefetch_related("document")
    # It should also be possible to compare from the parent document revision
    try:
        revision_from = revisions.get(id=from_id, document=doc)
    except Revision.DoesNotExist:
        revision_from = get_object_or_404(revisions, id=from_id, document=doc.parent)

    revision_to = get_object_or_404(revisions, id=to_id, document=doc)

    context = {
        "document": doc,
        "revision_from": revision_from,
        "revision_to": revision_to,
    }

    if request.GET.get("raw", False):
        template = "wiki/includes/revision_diff_table.html"
    else:
        template = "wiki/compare_revisions.html"

    return render(request, template, context)


@ensure_wiki_domain
@never_cache
@csrf_exempt
@login_required
@require_POST
@process_document_path
def quick_review(request, document_slug, document_locale):
    """
    Quickly mark a revision as no longer needing a particular type
    of review.
    """
    doc = get_object_or_404(Document, locale=document_locale, slug=document_slug)

    rev_id = request.POST.get("revision_id")
    if not rev_id:
        raise Http404

    rev = get_object_or_404(Revision, pk=rev_id)

    if rev.id != doc.current_revision.id:
        # TODO: Find a better way to bail out of a collision.
        # Ideal is to kick them to the diff view, but that expects
        # fully-filled-out editing forms, and we don't have those
        # here.
        raise PermissionDenied(_("Document has been edited; please re-review."))

    needs_technical = rev.needs_technical_review
    needs_editorial = rev.needs_editorial_review

    request_technical = request.POST.get("request_technical", False)
    request_editorial = request.POST.get("request_editorial", False)

    messages = []
    new_tags = []
    if needs_technical:
        new_tags.append("technical")
    if needs_editorial:
        new_tags.append("editorial")

    if needs_technical and not request_technical:
        new_tags.remove("technical")
        messages.append("Technical review completed.")

    if needs_editorial and not request_editorial:
        new_tags.remove("editorial")
        messages.append("Editorial review completed.")

    if messages:
        # We approved something, make the new revision.
        data = {"summary": " ".join(messages), "comment": " ".join(messages)}
        new_rev = doc.revise(request.user, data=data)
        if new_tags:
            new_rev.review_tags.set(*new_tags)
        else:
            new_rev.review_tags.clear()
    return redirect(doc)


@never_cache
@ensure_wiki_domain
@api_view(["GET", "HEAD", "POST"])
@authentication_classes([TokenAuthentication])
@process_document_path
def revision_api(request, document_slug, document_locale):
    """
    GET a document's raw HTML with select macros rendered or removed, or
    POST new raw HTML to a document. POST's are allowed only for clients
    using a valid token passed via the "Authorization" header. The "ETag"
    header is returned, and conditional requests handled for both GET and
    POST requests, but conditional request handling is only intended for
    POST requests to avoid collisions.
    """
    doc = get_object_or_404(Document, slug=document_slug, locale=document_locale)

    if request.method == "POST":
        if not (request.auth and request.user.is_authenticated):
            return HttpResponseForbidden()
        content_type = request.content_type
        if content_type.startswith("application/json"):
            encoding = request.encoding or settings.DEFAULT_CHARSET
            data = json.loads(request.body.decode(encoding=encoding))
        elif content_type.startswith("multipart/form-data") or content_type.startswith(
            "application/x-www-form-urlencoded"
        ):
            data = request.POST
        else:
            return HttpResponseBadRequest(
                'POST body must be of type "application/json", '
                '"application/x-www-form-urlencoded", or "multipart/form-data".'
            )
        return do_revision_api_post(request, doc, data)

    mode = request.GET.get("mode")
    select_macros = request.GET.get("macros")

    if mode:
        if mode not in ("render", "remove"):
            return HttpResponseBadRequest(
                'The "mode" query parameter must be "render" or "remove".'
            )
        if not select_macros:
            return HttpResponseBadRequest(
                "Please specify one or more comma-separated macro names via "
                'the "macros" query parameter.'
            )
    elif select_macros:
        return HttpResponseBadRequest('Please specify a "mode" query parameter.')

    if select_macros:
        # Convert potentially comma-separated macro names into a list.
        select_macros = select_macros.replace(",", " ").split()

    return do_revision_api_get(request, doc, mode, select_macros)


def get_etag(request, doc, *args):
    """
    Returns the id of the document's current revision as a string.
    """
    return str(doc.current_revision.id)


@etag(get_etag)
def do_revision_api_get(request, doc, mode, select_macros):
    """
    Handles the GET, including adding the ETag header, assuming that
    validation has already been performed.
    """
    if mode and select_macros:
        html, _ = kumascript.get(
            doc, base_url=None, selective_mode=(mode, select_macros)
        )
    else:
        html, _ = doc.html, []
    response = HttpResponse(html)
    response["X-Frame-Options"] = "deny"
    response["X-Robots-Tag"] = "noindex"
    return response


@etag(get_etag)
def do_revision_api_post(request, doc, data):
    """
    Handles the POST, including conditional POST's, given the document and
    the POST data, assuming that the checks for a valid authorization token
    and acceptable POST data have already been made.
    """
    # Create a new revision and make it the document's current revision.
    doc.revise(request.user, data)
    # Schedule an immediate re-rendering of the document.
    doc.schedule_rendering(cache_control="max-age=0")
    # Schedule event notifications.
    EditDocumentEvent(doc.current_revision).fire(exclude=request.user)
    response = HttpResponse(doc.html, status=201)
    rev_url = f"{doc.get_absolute_url()}$revision/{doc.current_revision.id}"
    response["Location"] = request.build_absolute_uri(rev_url)
    # Set the "ETag" header or else the "etag" decorator will set it according
    # to the document's previous revision, i.e. the current revision prior to
    # the "revise" method call above.
    response["ETag"] = f'"{str(doc.current_revision.id)}"'
    return response
