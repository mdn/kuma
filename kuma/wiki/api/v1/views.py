from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from kuma.wiki.models import Document


@never_cache
@require_GET
def doc(request, locale, slug):
    """
    Return a JSON object that includes document content and metadata
    for the document specified by the locale and path. Raises a 404
    error if no such document exists. This is an API with URL
    /api/v1/doc/<locale>/<path>
    """
    document = get_object_or_404(Document, locale=locale, slug=slug)
    translations = document.get_other_translations(
        fields=('locale', 'slug', 'title'))

    return JsonResponse({
        'locale': locale,
        'slug': slug,
        'id': document.id,
        'title': document.title,
        'summary': document.get_summary_html(),
        'language': document.language,
        'absoluteURL': document.get_absolute_url(),
        'redirectURL': document.get_redirect_url(),
        'editURL': document.get_edit_url(),
        'bodyHTML': document.get_body_html(),
        'quickLinksHTML': document.get_quick_links_html(),
        'tocHTML': document.get_toc_html(),
        'parents': [
            {
                'url': d.get_absolute_url(),
                'title': d.title
            } for d in document.parents
        ],
        'translations': [
            {
                'locale': t.locale,
                'url': t.get_absolute_url(),
                'title': t.title
            } for t in translations
        ]
    })
