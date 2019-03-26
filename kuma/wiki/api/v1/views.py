from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import activate, ugettext as _
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from kuma.wiki.models import Document


def document_api_data(document):
    translations = document.get_other_translations(
        fields=('locale', 'slug', 'title'))

    return {
        'locale': document.locale,
        'slug': document.slug,
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
                'language': t.language,
                'localizedLanguage': _(settings.LOCALES[t.locale].english),
                'locale': t.locale,
                'url': t.get_absolute_url(),
                'title': t.title
            } for t in translations
        ],
        'contributors': [ c['username'] for c in document.contributors ],
        'lastModified': document.current_revision.created.isoformat(),
        'lastModifiedBy': (document.current_revision.creator and
                           str(document.current_revision.creator))
    }


@never_cache
@require_GET
def doc(request, locale, slug):
    """
    Return a JSON object that includes document content and metadata
    for the document specified by the locale and path. Raises a 404
    error if no such document exists. This is an API with URL
    /api/v1/doc/<locale>/<path>
    """
    # TODO: This API endpoint probably needs to handle redirect documents
    # and documents that fall back to the en-US locale. See
    # the document() function in wiki/views/document.py for a model to follow.

    # Since we don't have the locale at the start of the path, our
    # locale middleware can't set the translation language correctly
    # and we need to do it explicitly. (We need to know the language
    # so that we can provide translated language names for the
    # translations menu.)
    activate(locale)
    document = get_object_or_404(Document, locale=locale, slug=slug)
    return JsonResponse(document_api_data(document))
