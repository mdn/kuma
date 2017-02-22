# -*- coding: utf-8 -*-
import json

try:
    from cStringIO import cStringIO as StringIO
except ImportError:
    from StringIO import StringIO

import newrelic.agent
from constance import config
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import (Http404, HttpResponse, HttpResponseBadRequest,
                         HttpResponsePermanentRedirect, JsonResponse)
from django.http.multipartparser import MultiPartParser
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import urlunquote_plus
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import (condition, require_GET,
                                          require_http_methods, require_POST)
from pyquery import PyQuery as pq

import kuma.wiki.content
from kuma.authkeys.decorators import accepts_auth_key
from kuma.core.decorators import (block_user_agents, login_required,
                                  permission_required, superuser_required,
                                  redirect_in_maintenance_mode)
from kuma.core.urlresolvers import reverse
from kuma.core.utils import urlparams
from kuma.search.store import get_search_url_from_referer

from .. import kumascript
from ..constants import SLUG_CLEANSING_RE
from ..decorators import (allow_CORS_GET, check_readonly, prevent_indexing,
                          process_document_path)
from ..events import EditDocumentEvent, EditDocumentInTreeEvent
from ..forms import TreeMoveForm
from ..models import (Document, DocumentDeletionLog,
                      DocumentRenderedContentNotAvailable, DocumentZone)
from ..tasks import move_page
from .utils import document_last_modified, split_slug


def _get_html_and_errors(request, doc, rendering_params):
    """
    Get the initial HTML for a Document, including determining whether
    to use kumascript to render it.

    """
    doc_html, ks_errors = doc.html, None
    render_raw_fallback = False
    base_url = request.build_absolute_uri('/')

    if rendering_params['use_rendered']:
        if (request.GET.get('bleach_new', False) is not False and
                request.user.is_authenticated()):
            # Temporary bleach_new query option to switch to Constance-based
            # Bleach whitelists, uses KumaScript POST for temporary rendering
            doc_html, ks_errors = kumascript.post(request, doc_html,
                                                  request.LANGUAGE_CODE, True)

        else:
            # A logged-in user can schedule a full re-render with Shift-Reload
            cache_control = None
            if request.user.is_authenticated():
                # Shift-Reload sends Cache-Control: no-cache
                ua_cc = request.META.get('HTTP_CACHE_CONTROL')
                if ua_cc == 'no-cache':
                    cache_control = 'no-cache'

            try:
                r_body, r_errors = doc.get_rendered(cache_control, base_url)
                if r_body:
                    doc_html = r_body
                if r_errors:
                    ks_errors = r_errors
            except DocumentRenderedContentNotAvailable:
                # There was no rendered content available, and we were unable
                # to render it on the spot. So, fall back to presenting raw
                # content
                render_raw_fallback = True

    return doc_html, ks_errors, render_raw_fallback


def _make_doc_structure(document, level, expand, depth):
    if document.is_redirect:
        return None

    if expand:
        result = dict(document.get_json_data())
        result['subpages'] = []
    else:
        result = {
            'title': document.title,
            'slug': document.slug,
            'locale': document.locale,
            'url': document.get_absolute_url(),
            'subpages': []
        }

    if level < depth:
        descendants = document.get_descendants(1)
        descendants.sort(key=lambda item: item.title)
        for descendant in descendants:
            subpage = _make_doc_structure(descendant, level + 1, expand, depth)
            if subpage is not None:
                result['subpages'].append(subpage)
    return result


def _get_seo_parent_title(slug_dict, document_locale):
    """
    Get parent-title information for SEO purposes.
    """
    if slug_dict['seo_root']:
        try:
            seo_root_doc = Document.objects.get(locale=document_locale,
                                                slug=slug_dict['seo_root'])
            return u' - %s' % seo_root_doc.title
        except Document.DoesNotExist:
            pass
    return ''


def _filter_doc_html(request, doc, doc_html, rendering_params):
    """
    Apply needed filtering/annotating operations to a Document's HTML.
    """
    # If ?summary is on, just serve up the summary as doc HTML
    if rendering_params['summary']:
        return doc.get_summary_html()

    # Shortcut the parsing & filtering, if none of these relevant rendering
    # params are set.
    if not (rendering_params['section'] or rendering_params['raw'] or
            rendering_params['edit_links'] or rendering_params['include']):
        return doc_html

    # TODO: One more view-time content parsing instance to refactor
    tool = kuma.wiki.content.parse(doc_html)

    # ?raw view is often used for editors - apply safety filtering.
    # TODO: Should this stuff happen in render() itself?
    if rendering_params['raw']:
        # HACK: Raw rendered content has not had section IDs injected
        tool.injectSectionIDs()
        tool.filterEditorSafety()

    # If a section ID is specified, extract that section.
    # TODO: Pre-extract every section on render? Might be over-optimization
    if rendering_params['section']:
        tool.extractSection(rendering_params['section'])

    # If this user can edit the document, inject section editing links.
    # TODO: Rework so that this happens on the client side?
    if ((rendering_params['edit_links'] or not rendering_params['raw']) and
            request.user.is_authenticated() and
            doc.allows_revision_by(request.user)):
        tool.injectSectionEditingLinks(doc.slug, doc.locale)

    doc_html = tool.serialize()

    # If this is an include, filter out the class="noinclude" blocks.
    # TODO: Any way to make this work in rendering? Possibly over-optimization,
    # because this is often paired with ?section - so we'd need to store every
    # section twice for with & without include sections
    if rendering_params['include']:
        doc_html = kuma.wiki.content.filter_out_noinclude(doc_html)

    return doc_html


def _set_common_headers(doc, section_id, response):
    """
    Perform some response-header manipulation that gets used in
    several places.
    """
    response['ETag'] = doc.calculate_etag(section_id)
    if doc.current_revision_id:
        response['X-kuma-revision'] = doc.current_revision_id
    return response


def _default_locale_fallback(request, document_slug, document_locale):
    """
    If we're falling back to a Document in the default locale, figure
    out why and whether we can redirect to a translation in the
    requested locale.

    """
    fallback_doc = None
    redirect_url = None
    fallback_reason = None

    try:
        fallback_doc = Document.objects.get(locale=settings.WIKI_DEFAULT_LANGUAGE,
                                            slug=document_slug)

        # If there's a translation to the requested locale, take it:
        translation = fallback_doc.translated_to(document_locale)

        if translation and translation.current_revision:
            url = translation.get_absolute_url()
            redirect_url = urlparams(url, query_dict=request.GET)
        elif translation and fallback_doc.current_revision:
            # Found a translation but its current_revision is None
            # and OK to fall back to parent (parent is approved).
            fallback_reason = 'translation_not_approved'
        elif fallback_doc.current_revision:
            # There is no translation
            # and OK to fall back to parent (parent is approved).
            fallback_reason = 'no_translation'
    except Document.DoesNotExist:
        pass

    return fallback_doc, fallback_reason, redirect_url


def _get_doc_and_fallback_reason(document_locale, document_slug):
    """
    Attempt to fetch a Document at the given locale and slug, and
    return it, or return a fallback reason if we weren't able to.

    """
    doc = None
    fallback_reason = None

    try:
        doc = Document.objects.get(locale=document_locale, slug=document_slug)
        if (not doc.current_revision and doc.parent and
                doc.parent.current_revision):
            # This is a translation but its current_revision is None
            # and OK to fall back to parent (parent is approved).
            fallback_reason = 'translation_not_approved'
        elif not doc.current_revision:
            fallback_reason = 'no_content'
    except Document.DoesNotExist:
        pass

    return doc, fallback_reason


@block_user_agents
@require_GET
@allow_CORS_GET
@process_document_path
def children(request, document_slug, document_locale):
    """
    Retrieves a document and returns its children in a JSON structure
    """
    expand = 'expand' in request.GET
    max_depth = 5
    depth = int(request.GET.get('depth', max_depth))
    if depth > max_depth:
        depth = max_depth

    result = []
    try:
        doc = Document.objects.get(locale=document_locale,
                                   slug=document_slug)
        result = _make_doc_structure(doc, 0, expand, depth)
        if result is None:
            result = {'error': 'Document has moved.'}
    except Document.DoesNotExist:
        result = {'error': 'Document does not exist.'}

    return JsonResponse(result)


@block_user_agents
@require_http_methods(['GET', 'POST'])
@permission_required('wiki.move_tree')
@process_document_path
@check_readonly
@prevent_indexing
def move(request, document_slug, document_locale):
    """
    Move a tree of pages
    """
    doc = get_object_or_404(Document,
                            locale=document_locale,
                            slug=document_slug)

    descendants = doc.get_descendants()
    slug_split = split_slug(doc.slug)

    if request.method == 'POST':
        form = TreeMoveForm(initial=request.GET, data=request.POST)
        if form.is_valid():
            conflicts = doc._tree_conflicts(form.cleaned_data['slug'])
            if conflicts:
                return render(request, 'wiki/move.html', {
                    'form': form,
                    'document': doc,
                    'descendants': descendants,
                    'descendants_count': len(descendants),
                    'conflicts': conflicts,
                    'SLUG_CLEANSING_RE': SLUG_CLEANSING_RE,
                })
            move_page.delay(document_locale, document_slug,
                            form.cleaned_data['slug'],
                            request.user.id)
            return render(request, 'wiki/move_requested.html', {
                'form': form,
                'document': doc
            })
    else:
        form = TreeMoveForm()

    return render(request, 'wiki/move.html', {
        'form': form,
        'document': doc,
        'descendants': descendants,
        'descendants_count': len(descendants),
        'SLUG_CLEANSING_RE': SLUG_CLEANSING_RE,
        'specific_slug': slug_split['specific']
    })


@block_user_agents
@process_document_path
@check_readonly
@superuser_required
def repair_breadcrumbs(request, document_slug, document_locale):
    doc = get_object_or_404(Document,
                            locale=document_locale,
                            slug=document_slug)
    doc.repair_breadcrumbs()
    return redirect(doc.get_absolute_url())


@require_GET
@allow_CORS_GET
@process_document_path
@prevent_indexing
def toc(request, document_slug=None, document_locale=None):
    """
    Return a document's table of contents as HTML.
    """
    query = {
        'locale': request.LANGUAGE_CODE,
        'current_revision__isnull': False,
    }
    if document_slug is not None:
        query['slug'] = document_slug
        query['locale'] = document_locale
    elif 'title' in request.GET:
        query['title'] = request.GET['title']
    elif 'slug' in request.GET:
        query['slug'] = request.GET['slug']
    else:
        return HttpResponseBadRequest()

    document = get_object_or_404(Document, **query)
    toc_html = document.get_toc_html()
    if toc_html:
        toc_html = '<ol>' + toc_html + '</ol>'

    return HttpResponse(toc_html)


@block_user_agents
@require_GET
@allow_CORS_GET
@process_document_path
@prevent_indexing
def as_json(request, document_slug=None, document_locale=None):
    """
    Return some basic document info in a JSON blob.
    """
    kwargs = {
        'locale': request.LANGUAGE_CODE,
        'current_revision__isnull': False,
    }
    if document_slug is not None:
        kwargs['slug'] = document_slug
        kwargs['locale'] = document_locale
    elif 'title' in request.GET:
        kwargs['title'] = request.GET['title']
    elif 'slug' in request.GET:
        kwargs['slug'] = request.GET['slug']
    else:
        return HttpResponseBadRequest()

    document = get_object_or_404(Document, **kwargs)
    (kuma.wiki.content.parse(document.html)
                      .injectSectionIDs()
                      .serialize())

    stale = True
    if request.user.is_authenticated():
        # A logged-in user can demand fresh data with a shift-refresh
        # Shift-Reload sends Cache-Control: no-cache
        ua_cc = request.META.get('HTTP_CACHE_CONTROL')
        if ua_cc == 'no-cache':
            stale = False

    data = document.get_json_data(stale=stale)
    return JsonResponse(data)


@block_user_agents
@require_GET
@allow_CORS_GET
@process_document_path
@prevent_indexing
def styles(request, document_slug=None, document_locale=None):
    """
    Return the Document zone stylsheet.
    """
    kwargs = {'slug': document_slug, 'locale': document_locale}
    document = get_object_or_404(Document, **kwargs)
    zone = get_object_or_404(DocumentZone, document=document)
    return HttpResponse(zone.styles, content_type='text/css')


@block_user_agents
@require_POST
@login_required
@process_document_path
def subscribe(request, document_slug, document_locale):
    """
    Toggle watching a document for edits.
    """
    document = get_object_or_404(
        Document, locale=document_locale, slug=document_slug)
    status = 0

    if EditDocumentEvent.is_notifying(request.user, document):
        EditDocumentEvent.stop_notifying(request.user, document)
    else:
        EditDocumentEvent.notify(request.user, document)
        status = 1

    if request.is_ajax():
        return JsonResponse({'status': status})
    else:
        return redirect(document)


@block_user_agents
@require_POST
@login_required
@process_document_path
def subscribe_to_tree(request, document_slug, document_locale):
    """
    Toggle watching a tree of documents for edits.
    """
    document = get_object_or_404(
        Document, locale=document_locale, slug=document_slug)
    status = 0

    if EditDocumentInTreeEvent.is_notifying(request.user, document):
        EditDocumentInTreeEvent.stop_notifying(request.user, document)
    else:
        EditDocumentInTreeEvent.notify(request.user, document)
        status = 1

    if request.is_ajax():
        return JsonResponse({'status': status})
    else:
        return redirect(document)


def _document_redirect_to_create(document_slug, document_locale, slug_dict):
    """
    When a Document doesn't exist but the user can create it, return
    the creation URL to redirect to.
    """
    url = reverse('wiki.create', locale=document_locale)
    if slug_dict['length'] > 1:
        parent_doc = get_object_or_404(Document,
                                       locale=document_locale,
                                       slug=slug_dict['parent'],
                                       is_template=0)
        url = urlparams(url, parent=parent_doc.id,
                        slug=slug_dict['specific'])
    else:
        # This is a "base level" redirect, i.e. no parent
        url = urlparams(url, slug=document_slug)
    return url


@newrelic.agent.function_trace()
@allow_CORS_GET
@prevent_indexing
def _document_deleted(request, deletion_logs):
    """When a Document has been deleted return a 404.

    If the user can restore documents, then return a 404 but also include the
    template with the form to restore the document.

    """
    if request.user and request.user.has_perm('wiki.restore_document'):
        deletion_log = deletion_logs.order_by('-pk')[0]
        context = {'deletion_log': deletion_log}
        return render(request, 'wiki/deletion_log.html', context, status=404)

    raise Http404


@newrelic.agent.function_trace()
@allow_CORS_GET
def _document_raw(request, doc, doc_html, rendering_params):
    """
    Display a raw Document.
    """
    response = HttpResponse(doc_html)
    response['X-Frame-Options'] = 'Allow'
    response['X-Robots-Tag'] = 'noindex'
    absolute_url = urlunquote_plus(doc.get_absolute_url())

    if absolute_url in (config.KUMA_CUSTOM_SAMPLE_CSS_PATH):
        response['Content-Type'] = 'text/css; charset=utf-8'
    elif doc.is_template:
        # Treat raw, un-bleached template source as plain text, not HTML.
        response['Content-Type'] = 'text/plain; charset=utf-8'

    return _set_common_headers(doc, rendering_params['section'], response)


@csrf_exempt
@require_http_methods(['GET', 'PUT', 'HEAD'])
@redirect_in_maintenance_mode(methods=['PUT'])
@allow_CORS_GET
@accepts_auth_key
@process_document_path
@condition(last_modified_func=document_last_modified)
@newrelic.agent.function_trace()
def document(request, document_slug, document_locale):
    """
    View a wiki document.
    """
    # PUT requests go to the write API.
    if request.method == 'PUT':
        if (not request.authkey and not request.user.is_authenticated()):
            raise PermissionDenied
        return _document_PUT(request,
                             document_slug,
                             document_locale)

    fallback_reason = None
    slug_dict = split_slug(document_slug)

    # Is there a document at this slug, in this locale?
    doc, fallback_reason = _get_doc_and_fallback_reason(document_locale,
                                                        document_slug)

    if doc is None:
        # Possible the document once existed, but is now deleted.
        # If so, show that it was deleted.
        deletion_log_entries = DocumentDeletionLog.objects.filter(
            locale=document_locale,
            slug=document_slug
        )
        if deletion_log_entries.exists():
            return _document_deleted(request, deletion_log_entries)

        # We can throw a 404 immediately if the request type is HEAD.
        # TODO: take a shortcut if the document was found?
        if request.method == 'HEAD':
            raise Http404

        # Check if we should fall back to default locale.
        fallback_doc, fallback_reason, redirect_url = _default_locale_fallback(
            request, document_slug, document_locale)
        if fallback_doc is not None:
            doc = fallback_doc
            if redirect_url is not None:
                return redirect(redirect_url)
        else:
            # If a Document is not found, we may 404 immediately based on
            # request parameters.
            if (any([request.GET.get(param, None)
                     for param in ('raw', 'include', 'nocreate')]) or
                    not request.user.is_authenticated()):
                raise Http404

            # The user may be trying to create a child page; if a parent exists
            # for this document, redirect them to the "Create" page
            # Otherwise, they could be trying to create a main level doc.
            create_url = _document_redirect_to_create(document_slug,
                                                      document_locale,
                                                      slug_dict)
            return redirect(create_url)

    # We found a Document. Now we need to figure out how we're going
    # to display it.

    # If we're a redirect, and redirecting hasn't been disabled, redirect.

    # Obey explicit redirect pages:
    # Don't redirect on redirect=no (like Wikipedia), so we can link from a
    # redirected-to-page back to a "Redirected from..." link, so you can edit
    # the redirect.
    redirect_url = (None if request.GET.get('redirect') == 'no'
                    else doc.get_redirect_url())

    if redirect_url and redirect_url != doc.get_absolute_url():
        url = urlparams(redirect_url, query_dict=request.GET)
        # TODO: Re-enable the link in this message after Django >1.5 upgrade
        # Redirected from <a href="%(url)s?redirect=no">%(url)s</a>
        messages.add_message(
            request, messages.WARNING,
            mark_safe(ugettext(u'Redirected from %(url)s') % {
                "url": request.build_absolute_uri(doc.get_absolute_url())
            }), extra_tags='wiki_redirect')
        return HttpResponsePermanentRedirect(url)

    # Read some request params to see what we're supposed to do.
    rendering_params = {}
    for param in ('raw', 'summary', 'include', 'edit_links'):
        rendering_params[param] = request.GET.get(param, False) is not False
    rendering_params['section'] = request.GET.get('section', None)
    rendering_params['render_raw_fallback'] = False
    rendering_params['use_rendered'] = kumascript.should_use_rendered(doc, request.GET)

    # Get us some HTML to play with.
    doc_html, ks_errors, render_raw_fallback = _get_html_and_errors(
        request, doc, rendering_params)
    rendering_params['render_raw_fallback'] = render_raw_fallback
    toc_html = None

    # Start parsing and applying filters.
    if not doc.is_template:
        if doc.show_toc and not rendering_params['raw']:
            toc_html = doc.get_toc_html()
        else:
            toc_html = None
        doc_html = _filter_doc_html(request, doc, doc_html, rendering_params)

    # If we're doing raw view, bail out to that now.
    if rendering_params['raw']:
        return _document_raw(request, doc, doc_html, rendering_params)

    # Get the SEO summary
    seo_summary = ''
    if not doc.is_template:
        seo_summary = doc.get_summary_text()

    # Get the additional title information, if necessary.
    seo_parent_title = _get_seo_parent_title(slug_dict, document_locale)

    # Retrieve pre-parsed content hunks
    if doc.is_template:
        quick_links_html, zone_subnav_html = None, None
        body_html = doc_html
    else:
        quick_links_html = doc.get_quick_links_html()
        zone_subnav_html = doc.get_zone_subnav_html()
        body_html = doc.get_body_html()

    share_text = ugettext(
        'I learned about %(title)s on MDN.') % {"title": doc.title}

    contributors = doc.contributors
    contributors_count = len(contributors)
    has_contributors = contributors_count > 0

    # Bundle it all up and, finally, return.
    context = {
        'document': doc,
        'document_html': doc_html,
        'toc_html': toc_html,
        'quick_links_html': quick_links_html,
        'zone_subnav_html': zone_subnav_html,
        'body_html': body_html,
        'contributors': contributors,
        'contributors_count': contributors_count,
        'contributors_limit': 6,
        'has_contributors': has_contributors,
        'fallback_reason': fallback_reason,
        'kumascript_errors': ks_errors,
        'render_raw_fallback': rendering_params['render_raw_fallback'],
        'seo_summary': seo_summary,
        'seo_parent_title': seo_parent_title,
        'share_text': share_text,
        'search_url': get_search_url_from_referer(request) or '',
        'analytics_page_revision': doc.current_revision_id,
    }
    response = render(request, 'wiki/document.html', context)
    return _set_common_headers(doc, rendering_params['section'], response)


def _document_PUT(request, document_slug, document_locale):
    """Handle PUT requests as document write API"""

    # Try parsing one of the supported content types from the request
    try:
        content_type = request.META.get('CONTENT_TYPE', '')

        if content_type.startswith('application/json'):
            data = json.loads(request.body)

        elif content_type.startswith('multipart/form-data'):
            parser = MultiPartParser(request.META,
                                     StringIO(request.body),
                                     request.upload_handlers,
                                     request.encoding)
            data, files = parser.parse()

        elif content_type.startswith('text/html'):
            # TODO: Refactor this into wiki.content ?
            # First pass: Just assume the request body is an HTML fragment.
            html = request.body
            data = dict(content=html)

            # Second pass: Try parsing the body as a fuller HTML document,
            # and scrape out some of the interesting parts.
            try:
                doc = pq(html)
                head_title = doc.find('head title')
                if head_title.length > 0:
                    data['title'] = head_title.text()
                body_content = doc.find('body')
                if body_content.length > 0:
                    data['content'] = body_content.html()
            except Exception:
                pass

        else:
            resp = HttpResponse()
            resp.status_code = 400
            resp.content = ugettext(
                "Unsupported content-type: %s") % content_type
            return resp

    except Exception as e:
        resp = HttpResponse()
        resp.status_code = 400
        resp.content = ugettext("Request parsing error: %s") % e
        return resp

    try:
        # Look for existing document to edit:
        doc = Document.objects.get(locale=document_locale,
                                   slug=document_slug)
        if not doc.allows_revision_by(request.user):
            raise PermissionDenied
        section_id = request.GET.get('section', None)
        is_new = False

        # Use ETags to detect mid-air edit collision
        # see: http://www.w3.org/1999/04/Editing/
        expected_etag = request.META.get('HTTP_IF_MATCH', False)
        if expected_etag:
            curr_etag = doc.calculate_etag(section_id)
            if curr_etag != expected_etag:
                resp = HttpResponse()
                resp.status_code = 412
                resp.content = ugettext('ETag precondition failed')
                return resp

    except Document.DoesNotExist:
        # No existing document, so this is an attempt to create a new one...
        if not Document.objects.allows_add_by(request.user, document_slug):
            raise PermissionDenied

        # TODO: There should be a model utility for creating a doc...

        # Let's see if this slug path implies a parent...
        slug_parts = split_slug(document_slug)
        if not slug_parts['parent']:
            # Apparently, this is a root page!
            parent_doc = None
        else:
            # There's a parent implied, so make sure we can find it.
            parent_doc = get_object_or_404(Document, locale=document_locale,
                                           slug=slug_parts['parent'])

        # Create and save the new document; we'll revise it immediately.
        doc = Document(slug=document_slug, locale=document_locale,
                       title=data.get('title', document_slug),
                       parent_topic=parent_doc)
        doc.save()
        section_id = None  # No section editing for new document!
        is_new = True

    new_rev = doc.revise(request.user, data, section_id)
    doc.schedule_rendering('max-age=0')

    request.authkey.log(is_new and 'created' or 'updated',
                        new_rev, data.get('summary', None))

    resp = HttpResponse()
    if not is_new:
        resp.content = 'RESET'
        resp.status_code = 205
    else:
        resp.content = 'CREATED'
        new_loc = request.build_absolute_uri(doc.get_absolute_url())
        resp['Location'] = new_loc
        resp.status_code = 201

    return resp
