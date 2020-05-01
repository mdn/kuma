import newrelic.agent
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_GET

from kuma.core.decorators import (
    block_user_agents,
    ensure_wiki_domain,
    shared_cache_control,
)

from ..constants import ALLOWED_TAGS, REDIRECT_CONTENT
from ..decorators import allow_CORS_GET
from ..models import Document, EditorToolbar


@ensure_wiki_domain
@shared_cache_control
@require_GET
def ckeditor_config(request):
    """
    Return ckeditor config from database
    """
    default_config = EditorToolbar.objects.filter(name="default")
    if default_config.exists():
        code = default_config[0].code
    else:
        code = ""

    context = {
        "editor_config": code,
        "redirect_pattern": REDIRECT_CONTENT,
        "allowed_tags": " ".join(ALLOWED_TAGS),
    }
    return render(
        request,
        "wiki/ckeditor_config.js",
        context,
        content_type="application/x-javascript",
    )


@shared_cache_control
@newrelic.agent.function_trace()
@block_user_agents
@require_GET
@allow_CORS_GET
def autosuggest_documents(request):
    """
    Returns the closest title matches for front-end autosuggests
    """
    partial_title = request.GET.get("term", "")
    locale = request.GET.get("locale", False)
    current_locale = request.GET.get("current_locale", False)
    exclude_current_locale = request.GET.get("exclude_current_locale", False)

    if not partial_title:
        # Only handle actual autosuggest requests, not requests for a
        # memory-busting list of all documents.
        return HttpResponseBadRequest(
            _(
                "Autosuggest requires a partial "
                "title. For a full document "
                "index, see the main page."
            )
        )

    # Retrieve all documents that aren't redirects
    docs = (
        Document.objects.extra(select={"length": "Length(slug)"})
        .filter(title__icontains=partial_title, is_redirect=0)
        .exclude(slug__icontains="Talk:")  # Remove old talk pages
        .order_by("title", "length")
    )

    # All locales are assumed, unless a specific locale is requested or banned
    if locale:
        docs = docs.filter(locale=locale)
    if current_locale:
        docs = docs.filter(locale=request.LANGUAGE_CODE)
    if exclude_current_locale:
        docs = docs.exclude(locale=request.LANGUAGE_CODE)

    # Generates a list of acceptable docs
    docs_list = []
    for doc in docs[:100]:
        data = doc.get_json_data()
        data["label"] += " [" + doc.locale + "]"
        docs_list.append(data)

    return JsonResponse(docs_list, safe=False)
