from django.conf import settings
from django.http import HttpResponsePermanentRedirect, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import activate, ugettext as _
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET
from rest_framework import serializers, status
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from waffle.decorators import waffle_flag
from waffle.models import Flag, Sample, Switch

from kuma.api.v1.serializers import BCSignalSerializer
from kuma.core.urlresolvers import reverse
from kuma.search.filters import (
    HighlightFilterBackend,
    KeywordQueryBackend,
    LanguageFilterBackend,
    SearchQueryBackend,
    TagGroupFilterBackend)
from kuma.search.views import SearchView
from kuma.users.templatetags.jinja_helpers import gravatar_url
from kuma.wiki.models import Document
from kuma.wiki.templatetags.jinja_helpers import absolutify


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

    redirect = get_content_based_redirect(document)
    if redirect:
        redirect_url, is_redirect_to_document = redirect
        if is_redirect_to_document:
            return HttpResponsePermanentRedirect(redirect_url)
        return JsonResponse(document_api_data(redirect_url=redirect_url))

    return JsonResponse(document_api_data(document))


def get_s3_key(doc=None, locale=None, slug=None,
               prefix_with_forward_slash=False):
    if doc:
        locale, slug = doc.locale, doc.slug
    key = reverse('api.v1.doc', args=(locale, slug))
    if prefix_with_forward_slash:
        # Redirects within an S3 bucket must be prefixed with "/".
        return key
    return key.lstrip('/')


def get_cdn_key(locale, slug):
    """Given a document's locale and slug, return the "key" for the CDN."""
    return get_s3_key(locale=locale, slug=slug, prefix_with_forward_slash=True)


def get_content_based_redirect(document):
    """
    Returns None if the document is not a content-based redirect, otherwise a
    tuple pair comprising the redirect URL as well as a boolean value. The
    boolean value will be True if this is a redirect to another document,
    otherwise False. If the document is a redirect to another document or a
    redirect to the homepage, a relative URL will be returned, otherwise it
    will be a full URL to the wiki site.
    """
    redirect_url = document.get_redirect_url()
    if redirect_url and (redirect_url != document.get_absolute_url()):
        redirect_document = document.get_redirect_document(id_only=False)
        if redirect_document:
            # This is a redirect to another document.
            return (
                get_s3_key(redirect_document, prefix_with_forward_slash=True),
                True
            )
        # This is a redirect to non-document page. For now, if it's the home
        # page, return a relative path (so we stay on the read-only domain),
        # otherwise return the full URL for the wiki site.
        locale = document.locale
        is_home_page = (redirect_url in
                        ('/', '/' + locale, '/{}/'.format(locale)))
        if is_home_page:
            # Let's return a relative URL to the home page for this locale.
            return ('/{}/'.format(locale), False)
        # Otherwise, let's return a full URL to the Wiki site.
        return (absolutify(redirect_url, for_wiki_site=True), False)
    return None


def document_api_data(doc=None, redirect_url=None):
    """
    Returns the JSON data for the document for the document API.
    """
    if redirect_url:
        return {
            'documentData': None,
            'redirectURL': redirect_url,
        }

    # The original english slug for this document, for google analytics
    if doc.locale == 'en-US':
        en_slug = doc.slug
    elif doc.parent_id and doc.parent.locale == 'en-US':
        en_slug = doc.parent.slug
    else:
        en_slug = ''

    other_translations = doc.get_other_translations(
        fields=('locale', 'slug', 'title', 'parent'))
    available_locales = (
        set([doc.locale]) | set(t.locale for t in other_translations))

    doc_absolute_url = doc.get_absolute_url()
    return {
        'documentData': {
            'locale': doc.locale,
            'slug': doc.slug,
            'enSlug': en_slug,
            'id': doc.id,
            'title': doc.title,
            'summary': doc.get_summary_html(),
            'language': doc.language,
            'hrefLang': doc.get_hreflang(available_locales),
            'absoluteURL': doc_absolute_url,
            'wikiURL': absolutify(doc_absolute_url, for_wiki_site=True),
            'translateURL': (
                absolutify(
                    reverse(
                        'wiki.select_locale',
                        args=(doc.slug,),
                        locale=doc.locale,
                    ),
                    for_wiki_site=True
                )
                if doc.is_localizable else
                None
            ),
            'bodyHTML': doc.get_body_html(),
            'quickLinksHTML': doc.get_quick_links_html(),
            'tocHTML': doc.get_toc_html(),
            'parents': [
                {
                    'url': d.get_absolute_url(),
                    'title': d.title
                } for d in doc.parents
            ],
            'translations': [
                {
                    'language': t.language,
                    'hrefLang': t.get_hreflang(available_locales),
                    'localizedLanguage': _(settings.LOCALES[t.locale].english),
                    'locale': t.locale,
                    'url': t.get_absolute_url(),
                    'title': t.title
                } for t in other_translations
            ],
            'lastModified': (doc.current_revision and
                             doc.current_revision.created.isoformat()),
        },
        'redirectURL': None,
    }


@never_cache
@require_GET
def whoami(request):
    """
    Return a JSON object representing the current user, either
    authenticated or anonymous.
    """
    user = request.user
    if user.is_authenticated:
        data = {
            'username': user.username,
            'timezone': user.timezone,
            'is_authenticated': True,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'is_beta_tester': user.is_beta_tester,
            'gravatar_url': {
                'small': gravatar_url(user.email, size=50),
                'large': gravatar_url(user.email, size=200),
            }
        }
    else:
        data = {
            'username': None,
            'timezone': settings.TIME_ZONE,
            'is_authenticated': False,
            'is_staff': False,
            'is_superuser': False,
            'is_beta_tester': False,
            'gravatar_url': {
                'small': None,
                'large': None,
            }
        }

    # Add waffle data to the dict we're going to be returning.
    # This is what the waffle.wafflejs() template tag does, but we're
    # doing it via an API instead of hardcoding the settings into
    # the HTML page. See also from waffle.views._generate_waffle_js.
    #
    # Note that if we upgrade django-waffle, version 15 introduces a
    # pluggable flag model, and the approved way to get all flag
    # objects will then become:
    #    get_waffle_flag_model().get_all()
    #
    data['waffle'] = {
        'flags': {f.name: f.is_active(request) for f in Flag.get_all()},
        'switches': {s.name: s.is_active() for s in Switch.get_all()},
        'samples': {s.name: s.is_active() for s in Sample.get_all()},
    }
    return JsonResponse(data)


class APIDocumentSerializer(serializers.Serializer):
    title = serializers.CharField(read_only=True, max_length=255)
    slug = serializers.CharField(read_only=True, max_length=255)
    locale = serializers.CharField(read_only=True, max_length=7)
    excerpt = serializers.ReadOnlyField(source='get_excerpt')


class APILanguageFilterBackend(LanguageFilterBackend):
    """Override of kuma.search.filters:LanguageFilterBackend that is almost
    exactly the same except the locale comes from custom code rather than
    via kuma.core.i18n.get_language_from_request because that can't be used
    in the API.

    Basically, it's the same exact functionality but ...
    """

    def filter_queryset(self, request, queryset, view):
        locale = request.GET.get('locale') or settings.LANGUAGE_CODE
        if locale not in settings.ACCEPTED_LOCALES:
            raise serializers.ValidationError(
                {'error': 'Not a valid locale code'})
        request.LANGUAGE_CODE = locale
        return super(APILanguageFilterBackend, self).filter_queryset(
            request, queryset, view)


class APISearchQueryBackend(SearchQueryBackend):
    """Override of kuma.search.filters.SearchQueryBackend that makes a
    stink if the 'q' query parameter is falsy."""

    def filter_queryset(self, request, queryset, view):
        search_term = (view.query_params.get('q') or '').strip()
        if not search_term:
            raise serializers.ValidationError(
                {'error': "Search term 'q' must be set"})
        return super(APISearchQueryBackend, self).filter_queryset(
            request, queryset, view)


class APISearchView(SearchView):
    serializer_class = APIDocumentSerializer
    renderer_classes = [JSONRenderer]
    filter_backends = (
        APISearchQueryBackend,
        KeywordQueryBackend,
        TagGroupFilterBackend,
        APILanguageFilterBackend,
        HighlightFilterBackend,
    )


search = never_cache(APISearchView.as_view())


@waffle_flag('bc-signals')
@api_view(['POST'])
@throttle_classes([UserRateThrottle])
def bc_signal(request):
    serializer = BCSignalSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.validated_data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
