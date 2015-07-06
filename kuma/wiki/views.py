# -*- coding: utf-8 -*-
from datetime import datetime
import json
import logging
import re
from urllib import urlencode

try:
    from cStringIO import cStringIO as StringIO
except:
    from StringIO import StringIO

import newrelic.agent
from pyquery import PyQuery as pq
from tower import ugettext_lazy as _lazy, ugettext as _

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import (HttpResponse, HttpResponseRedirect,
                         HttpResponsePermanentRedirect,
                         Http404, HttpResponseBadRequest)
from django.http.multipartparser import MultiPartParser
from django.shortcuts import (get_object_or_404, get_list_or_404,
                              redirect, render)
from django.utils.http import urlunquote_plus
from django.utils.safestring import mark_safe
from django.views.decorators.http import (require_GET, require_POST,
                                          require_http_methods, condition)
from django.views.decorators.clickjacking import (xframe_options_exempt,
                                                  xframe_options_sameorigin)
from django.views.decorators.csrf import csrf_exempt

from constance import config
from jingo.helpers import urlparams
from ratelimit.decorators import ratelimit
from smuggler.forms import ImportForm
from teamwork.shortcuts import get_object_or_404_or_403
import waffle

from kuma.authkeys.decorators import accepts_auth_key
from kuma.contentflagging.models import ContentFlag, FLAG_NOTIFICATIONS

from kuma.attachments.forms import AttachmentRevisionForm
from kuma.attachments.models import Attachment
from kuma.attachments.utils import attachments_json, full_attachment_url
from kuma.core.cache import memcache
from kuma.core.decorators import (never_cache, login_required,
                                  permission_required, superuser_required)
from kuma.core.urlresolvers import reverse
from kuma.core.utils import (get_object_or_none, paginate, smart_int,
                             get_ip, limit_banned_ip_to_0)
from kuma.search.store import referrer_url
from kuma.users.models import UserProfile

import kuma.wiki.content
from . import kumascript
from .constants import (DOCUMENTS_PER_PAGE, TEMPLATE_TITLE_PREFIX,
                        SLUG_CLEANSING_REGEX, REVIEW_FLAG_TAGS_DEFAULT,
                        DOCUMENT_LAST_MODIFIED_CACHE_KEY_TMPL,
                        REDIRECT_CONTENT, ALLOWED_TAGS)
from .decorators import (check_readonly, process_document_path,
                         allow_CORS_GET, prevent_indexing)
from .events import EditDocumentEvent
from .forms import (DocumentForm, RevisionForm, DocumentContentFlagForm,
                    RevisionValidationForm, TreeMoveForm,
                    DocumentDeletionForm)
from .helpers import format_comment
from .models import (Document, Revision, HelpfulVote, EditorToolbar,
                     DocumentZone, DocumentTag, ReviewTag, LocalizationTag,
                     DocumentDeletionLog,
                     DocumentRenderedContentNotAvailable,
                     RevisionIP)
from .queries import MultiQuerySet
from .tasks import move_page, send_first_edit_email
from .utils import locale_and_slug_from_path


log = logging.getLogger('kuma.wiki.views')


@newrelic.agent.function_trace()
def _document_last_modified(request, document_slug, document_locale):
    """
    Utility function to derive the last modified timestamp of a document.
    Mainly for the @condition decorator.
    """
    # build an adhoc natural cache key to not have to do DB query
    adhoc_natural_key = (document_locale, document_slug)
    natural_key_hash = Document.natural_key_hash(adhoc_natural_key)
    cache_key = DOCUMENT_LAST_MODIFIED_CACHE_KEY_TMPL % natural_key_hash
    try:
        last_mod = memcache.get(cache_key)
        if last_mod is None:
            doc = Document.objects.get(locale=document_locale,
                                       slug=document_slug)
            last_mod = doc.fill_last_modified_cache()

        # Convert the cached Unix epoch seconds back to Python datetime
        return datetime.fromtimestamp(float(last_mod))

    except Document.DoesNotExist:
        return None


def _split_slug(slug):
    """Utility function to do basic slug splitting"""
    slug_split = slug.split('/')
    length = len(slug_split)
    root = None

    seo_root = ''
    bad_seo_roots = ['Web']

    if length > 1:
        root = slug_split[0]

        if root in bad_seo_roots:
            if length > 2:
                seo_root = root + '/' + slug_split[1]
        else:
            seo_root = root

    specific = slug_split.pop()

    parent = '/'.join(slug_split)

    return {'specific': specific, 'parent': parent,
            'full': slug, 'parent_split': slug_split, 'length': length,
            'root': root, 'seo_root': seo_root}


def _join_slug(parent_split, slug):
    parent_split.append(slug)
    return '/'.join(parent_split)


#####################################################################
#
# Utility functions which support the document() view and its various
# sub-views.
#
#####################################################################


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


def _check_for_deleted_document(document_locale, document_slug):
    """
    If a Document is not found, see if there's a deletion log for it.

    """
    return DocumentDeletionLog.objects.filter(
        locale=document_locale,
        slug=document_slug
    )


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


def _document_redirect_to_create(document_slug, document_locale, slug_dict):
    """
    When a Document doesn't exist but the user can create it, return
    the creation URL to redirect to.

    """
    url = reverse('wiki.new_document', locale=document_locale)
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


def _check_404_params(request):
    """
    If a Document is not found, we may 404 immediately based on
    request parameters.

    """
    params = []
    for request_param in ('raw', 'include', 'nocreate'):
        params.append(request.GET.get(request_param, None))
    return any(params) or (not request.user.is_authenticated())


def _set_common_headers(doc, section_id, response):
    """
    Perform some response-header manipulation that gets used in
    several places.

    """
    response['ETag'] = doc.calculate_etag(section_id)
    if doc.current_revision_id:
        response['X-kuma-revision'] = doc.current_revision_id
    return response


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
                                                  request.locale, True)

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


def _generate_toc_html(doc, rendering_params):
    """
    Generate the HTML, if needed, for a Document's table of contents.

    """
    toc_html = None
    if doc.show_toc and not rendering_params['raw']:
        toc_html = doc.get_toc_html()
    return toc_html


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


def _get_seo_parent_title(slug_dict, document_locale):
    """
    Get parent-title information for SEO purposes.

    """
    if slug_dict['seo_root']:
        seo_root_doc = get_object_or_404(Document,
                                         locale=document_locale,
                                         slug=slug_dict['seo_root'])
        return u' - %s' % seo_root_doc.title
    else:
        return ''


#####################################################################
#
# Specialized sub-views which may be called by document().
#
#####################################################################


@newrelic.agent.function_trace()
@allow_CORS_GET
@prevent_indexing
def _document_deleted(request, deletion_logs):
    """
    When a Document has been deleted, display a notice.

    """
    deletion_log = deletion_logs.order_by('-pk')[0]
    context = {'deletion_log': deletion_log}
    return render(request, 'wiki/deletion_log.html', context, status=404)


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

    if absolute_url in (config.KUMA_CUSTOM_CSS_PATH,
                        config.KUMA_CUSTOM_SAMPLE_CSS_PATH):
        response['Content-Type'] = 'text/css; charset=utf-8'
    elif doc.is_template:
        # Treat raw, un-bleached template source as plain text, not HTML.
        response['Content-Type'] = 'text/plain; charset=utf-8'

    return _set_common_headers(doc, rendering_params['section'], response)


@csrf_exempt
@require_http_methods(['GET', 'PUT', 'HEAD'])
@allow_CORS_GET
@accepts_auth_key
@process_document_path
@condition(last_modified_func=_document_last_modified)
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
    slug_dict = _split_slug(document_slug)

    # Is there a document at this slug, in this locale?
    doc, fallback_reason = _get_doc_and_fallback_reason(document_locale,
                                                        document_slug)

    if doc is None:
        # Possible the document once existed, but is now deleted.
        # If so, show that it was deleted.
        deletion_logs = _check_for_deleted_document(document_locale,
                                                    document_slug)
        if deletion_logs.exists():
            return _document_deleted(request, deletion_logs)

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
            if _check_404_params(request):
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

    # Step 1: If we're a redirect, and redirecting hasn't been
    # disabled, redirect.

    # Obey explicit redirect pages:
    # Don't redirect on redirect=no (like Wikipedia), so we can link from a
    # redirected-to-page back to a "Redirected from..." link, so you can edit
    # the redirect.
    redirect_url = (None if request.GET.get('redirect') == 'no'
                    else doc.redirect_url())

    if redirect_url and redirect_url != doc.get_absolute_url():
        url = urlparams(redirect_url, query_dict=request.GET)
        # TODO: Re-enable the link in this message after Django >1.5 upgrade
        # Redirected from <a href="%(url)s?redirect=no">%(url)s</a>
        messages.add_message(
            request, messages.WARNING,
            mark_safe(_(u'Redirected from %(url)s') % {
                "url": request.build_absolute_uri(doc.get_absolute_url())
            }), extra_tags='wiki_redirect')
        return HttpResponsePermanentRedirect(url)

    # Step 2: Kick 'em out if they're not allowed to view this Document.
    if not request.user.has_perm('wiki.view_document', doc):
        raise PermissionDenied

    # Step 3: Read some request params to see what we're supposed to
    # do.
    rendering_params = {}
    for param in ('raw', 'summary', 'include', 'edit_links'):
        rendering_params[param] = request.GET.get(param, False) is not False
    rendering_params['section'] = request.GET.get('section', None)
    rendering_params['render_raw_fallback'] = False
    rendering_params['use_rendered'] = kumascript.should_use_rendered(doc, request.GET)

    # Step 4: Get us some HTML to play with.
    doc_html, ks_errors, render_raw_fallback = _get_html_and_errors(
        request, doc, rendering_params)
    rendering_params['render_raw_fallback'] = render_raw_fallback
    toc_html = None

    # Step 5: Start parsing and applying filters.
    if not doc.is_template:
        toc_html = _generate_toc_html(doc, rendering_params)
        doc_html = _filter_doc_html(request, doc, doc_html, rendering_params)

    # Step 6: If we're doing raw view, bail out to that now.
    if rendering_params['raw']:
        return _document_raw(request, doc, doc_html, rendering_params)

    # TODO: Port this kitsune feature over, eventually:
    #     https://github.com/jsocol/kitsune/commit/
    #       f1ebb241e4b1d746f97686e65f49e478e28d89f2

    # Get the SEO summary
    seo_summary = ''
    if not doc.is_template:
        seo_summary = doc.get_summary_text()

    # Get the additional title information, if necessary.
    seo_parent_title = _get_seo_parent_title(slug_dict, document_locale)

    # Retrieve file attachments
    attachments = attachments_json(doc.attachments)

    # Retrieve pre-parsed content hunks
    if doc.is_template:
        quick_links_html, zone_subnav_html = None, None
        body_html = doc_html
    else:
        quick_links_html = doc.get_quick_links_html()
        zone_subnav_html = doc.get_zone_subnav_html()
        body_html = doc.get_body_html()

    share_text = _('I learned about %(title)s on MDN.') % {"title": doc.title, }

    # Step 8: Bundle it all up and, finally, return.
    context = {
        'document': doc,
        'document_html': doc_html,
        'toc_html': toc_html,
        'quick_links_html': quick_links_html,
        'zone_subnav_html': zone_subnav_html,
        'body_html': body_html,
        'fallback_reason': fallback_reason,
        'kumascript_errors': ks_errors,
        'render_raw_fallback': rendering_params['render_raw_fallback'],
        'seo_summary': seo_summary,
        'seo_parent_title': seo_parent_title,
        'share_text': share_text,
        'attachment_data': attachments,
        'attachment_data_json': json.dumps(attachments),
        'search_url': referrer_url(request) or '',
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
            except:
                pass

        else:
            resp = HttpResponse()
            resp.status_code = 400
            resp.content = _("Unsupported content-type: %s") % content_type
            return resp

    except Exception, e:
        resp = HttpResponse()
        resp.status_code = 400
        resp.content = _("Request parsing error: %s") % e
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
                resp.content = _('ETag precondition failed')
                return resp

    except Document.DoesNotExist:
        # No existing document, so this is an attempt to create a new one...
        if not Document.objects.allows_add_by(request.user, document_slug):
            raise PermissionDenied

        # TODO: There should be a model utility for creating a doc...

        # Let's see if this slug path implies a parent...
        slug_parts = _split_slug(document_slug)
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
                       parent_topic=parent_doc,
                       category=Document.CATEGORIES[0][0])
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


@prevent_indexing
@process_document_path
@newrelic.agent.function_trace()
def revision(request, document_slug, document_locale, revision_id):
    """View a wiki document revision."""
    rev = get_object_or_404(Revision, pk=revision_id,
                            document__slug=document_slug)
    data = {'document': rev.document,
            'revision': rev,
            'comment': format_comment(rev)}
    return render(request, 'wiki/revision.html', data)


@require_GET
def list_documents(request, category=None, tag=None):
    """List wiki documents."""
    category_id = None
    if category:
        try:
            category_id = int(category)
            category = unicode(dict(Document.CATEGORIES)[category_id])
        except (KeyError, ValueError):
            raise Http404

    # Taggit offers a slug - but use name here, because the slugification
    # stinks and is hard to customize.
    tag_obj = None
    if tag:
        matching_tags = get_list_or_404(DocumentTag, name__iexact=tag)
        for matching_tag in matching_tags:
            if matching_tag.name.lower() == tag.lower():
                tag_obj = matching_tag
                break
    docs = Document.objects.filter_for_list(locale=request.locale,
                                            category=category_id,
                                            tag=tag_obj)
    paginated_docs = paginate(request, docs, per_page=DOCUMENTS_PER_PAGE)
    context = {
        'documents': paginated_docs,
        'count': docs.count(),
        'category': category,
        'tag': tag,
    }
    return render(request, 'wiki/list_documents.html', context)


@require_GET
def list_templates(request):
    """Returns listing of all templates"""
    docs = Document.objects.filter(is_template=True).order_by('title')
    paginated_docs = paginate(request, docs, per_page=DOCUMENTS_PER_PAGE)
    context = {
        'documents': paginated_docs,
        'count': docs.count(),
        'is_templates': True,
    }
    return render(request, 'wiki/list_documents.html', context)


@require_GET
def list_tags(request):
    """Returns listing of all tags"""
    tags = DocumentTag.objects.order_by('name')
    tags = paginate(request, tags, per_page=DOCUMENTS_PER_PAGE)
    return render(request, 'wiki/list_tags.html', {'tags': tags})


@require_GET
def list_documents_for_review(request, tag=None):
    """Lists wiki documents with revisions flagged for review"""
    tag_obj = tag and get_object_or_404(ReviewTag, name=tag) or None
    docs = Document.objects.filter_for_review(locale=request.locale, tag=tag_obj)
    paginated_docs = paginate(request, docs, per_page=DOCUMENTS_PER_PAGE)
    context = {
        'documents': paginated_docs,
        'count': docs.count(),
        'tag': tag_obj,
        'tag_name': tag,
    }
    return render(request, 'wiki/list_documents_for_review.html', context)


@require_GET
def list_documents_with_localization_tag(request, tag=None):
    """Lists wiki documents with localization tag"""
    tag_obj = tag and get_object_or_404(LocalizationTag, name=tag) or None
    docs = Document.objects.filter_with_localization_tag(locale=request.locale,
                                                         tag=tag_obj)
    paginated_docs = paginate(request, docs, per_page=DOCUMENTS_PER_PAGE)
    context = {
        'documents': paginated_docs,
        'count': docs.count(),
        'tag': tag_obj,
        'tag_name': tag,
    }
    return render(request, 'wiki/list_documents_with_localization_tags.html',
                  context)


@require_GET
def list_documents_with_errors(request):
    """Lists wiki documents with (KumaScript) errors"""
    docs = Document.objects.filter_for_list(locale=request.locale, errors=True)
    paginated_docs = paginate(request, docs, per_page=DOCUMENTS_PER_PAGE)
    context = {
        'documents': paginated_docs,
        'count': docs.count(),
        'errors': True,
    }
    return render(request, 'wiki/list_documents.html', context)


@require_GET
def list_documents_without_parent(request):
    """Lists wiki documents without parent (no English source document)"""
    docs = Document.objects.filter_for_list(locale=request.locale,
                                            noparent=True)
    paginated_docs = paginate(request, docs, per_page=DOCUMENTS_PER_PAGE)
    context = {
        'documents': paginated_docs,
        'count': docs.count(),
        'noparent': True,
    }
    return render(request, 'wiki/list_documents.html', context)


@require_GET
def list_top_level_documents(request):
    """Lists documents directly under /docs/"""
    docs = Document.objects.filter_for_list(locale=request.locale,
                                            toplevel=True)
    paginated_docs = paginate(request, docs, per_page=DOCUMENTS_PER_PAGE)
    context = {
        'documents': paginated_docs,
        'count': docs.count(),
        'toplevel': True,
    }
    return render(request, 'wiki/list_documents.html', context)


@login_required
@check_readonly
@prevent_indexing
@never_cache
@newrelic.agent.function_trace()
def new_document(request):
    """Create a new wiki document."""

    initial_slug = request.GET.get('slug', '')
    initial_title = initial_slug.replace('_', ' ')

    initial_parent_id = ''
    try:
        initial_parent_id = int(request.GET.get('parent', ''))
    except ValueError:
        pass

    clone_id = None
    try:
        clone_id = int(request.GET.get('clone', ''))
    except ValueError:
        pass

    if not Document.objects.allows_add_by(request.user, initial_slug):
        # Try to head off disallowed Template:* creation, right off the bat
        raise PermissionDenied

    is_template = initial_slug.startswith(TEMPLATE_TITLE_PREFIX)

    # If a parent ID is provided via GET, confirm it exists
    parent_slug = parent_path = ''

    if initial_parent_id:
        try:
            parent_doc = Document.objects.get(pk=initial_parent_id)
            parent_slug = parent_doc.slug
            parent_path = parent_doc.get_absolute_url()
        except Document.DoesNotExist:
            pass

    if request.method == 'GET':

        initial_data = {}
        initial_html = ''
        initial_tags = ''
        initial_toc = Revision.TOC_DEPTH_H4

        if clone_id:
            try:
                clone_doc = Document.objects.get(pk=clone_id)
                initial_title = clone_doc.title
                initial_html = clone_doc.html
                initial_tags = clone_doc.tags.all()
                if clone_doc.current_revision:
                    initial_toc = clone_doc.current_revision.toc_depth
                else:
                    initial_toc = 1

            except Document.DoesNotExist:
                pass

        if parent_slug:
            initial_data['parent_topic'] = initial_parent_id

        if initial_slug:
            initial_data['title'] = initial_title
            initial_data['slug'] = initial_slug

        if is_template:
            review_tags = ('template',)
        else:
            review_tags = REVIEW_FLAG_TAGS_DEFAULT

        doc_form = DocumentForm(initial=initial_data)

        rev_form = RevisionForm(initial={
            'slug': initial_slug,
            'title': initial_title,
            'content': initial_html,
            'review_tags': review_tags,
            'tags': initial_tags,
            'toc_depth': initial_toc
        })

        allow_add_attachment = (
            Attachment.objects.allow_add_attachment_by(request.user))
        context = {
            'is_template': is_template,
            'parent_slug': parent_slug,
            'parent_id': initial_parent_id,
            'document_form': doc_form,
            'revision_form': rev_form,
            'WIKI_DOCUMENT_TAG_SUGGESTIONS': config.WIKI_DOCUMENT_TAG_SUGGESTIONS,
            'initial_tags': initial_tags,
            'allow_add_attachment': allow_add_attachment,
            'attachment_form': AttachmentRevisionForm(),
            'parent_path': parent_path}

        return render(request, 'wiki/new_document.html', context)

    post_data = request.POST.copy()
    posted_slug = post_data['slug']
    post_data.update({'locale': request.locale})
    if parent_slug:
        post_data.update({'parent_topic': initial_parent_id})
        post_data.update({'slug': parent_slug + '/' + post_data['slug']})

    doc_form = DocumentForm(post_data)
    rev_form = RevisionValidationForm(request.POST.copy())
    rev_form.parent_slug = parent_slug

    if doc_form.is_valid() and rev_form.is_valid():
        rev_form = RevisionForm(post_data)
        if rev_form.is_valid():
            slug = doc_form.cleaned_data['slug']
            if not Document.objects.allows_add_by(request.user, slug):
                raise PermissionDenied

            doc = doc_form.save(None)
            _save_rev_and_notify(rev_form, request, doc)
            if doc.current_revision.is_approved:
                view = 'wiki.document'
            else:
                view = 'wiki.document_revisions'
            return HttpResponseRedirect(reverse(view, args=[doc.slug]))
        else:
            doc_form.data['slug'] = posted_slug
    else:
        doc_form.data['slug'] = posted_slug

    allow_add_attachment = (
        Attachment.objects.allow_add_attachment_by(request.user))
    context = {
        'is_template': is_template,
        'document_form': doc_form,
        'revision_form': rev_form,
        'WIKI_DOCUMENT_TAG_SUGGESTIONS': config.WIKI_DOCUMENT_TAG_SUGGESTIONS,
        'allow_add_attachment': allow_add_attachment,
        'attachment_form': AttachmentRevisionForm(),
        'parent_slug': parent_slug,
        'parent_path': parent_path}

    return render(request, 'wiki/new_document.html', context)


@require_http_methods(['GET', 'POST'])
@login_required  # TODO: Stop repeating this knowledge here and in Document.allows_editing_by.
@ratelimit(key='user', rate=limit_banned_ip_to_0, block=True)
@process_document_path
@check_readonly
@prevent_indexing
@never_cache
@newrelic.agent.function_trace()
def edit_document(request, document_slug, document_locale, revision_id=None):
    """Create a new revision of a wiki document, or edit document metadata."""
    doc = get_object_or_404_or_403('wiki.add_revision',
                                   request.user,
                                   Document,
                                   locale=document_locale,
                                   slug=document_slug)
    user = request.user

    # If this document has a parent, then the edit is handled by the
    # translate view. Pass it on.
    if doc.parent and doc.parent.id != doc.id:
        return translate(request, doc.parent.slug, doc.locale, revision_id,
                         bypass_process_document_path=True)
    if revision_id:
        rev = get_object_or_404(Revision, pk=revision_id, document=doc)
    else:
        rev = doc.current_revision or doc.revisions.order_by('-created',
                                                             '-id')[0]

    # Keep hold of the full post slug
    slug_dict = _split_slug(document_slug)
    # Update the slug, removing the parent path, and
    # *only* using the last piece.
    # This is only for the edit form.
    rev.slug = slug_dict['specific']

    section_id = request.GET.get('section', None)
    if section_id and not request.is_ajax():
        return HttpResponse(_("Sections may only be edited inline."))
    disclose_description = bool(request.GET.get('opendescription'))

    doc_form = rev_form = None
    if doc.allows_revision_by(user):
        rev_form = RevisionForm(instance=rev,
                                initial={'based_on': rev.id,
                                         'current_rev': rev.id,
                                         'comment': ''},
                                section_id=section_id)
    if doc.allows_editing_by(user):
        doc_form = DocumentForm(initial=_document_form_initial(doc))

    # Need to make check *here* to see if this could have a translation parent
    show_translation_parent_block = (
        (document_locale != settings.WIKI_DEFAULT_LANGUAGE) and
        (not doc.parent_id))

    if request.method == 'GET':
        if not (rev_form or doc_form):
            # You can't do anything on this page, so get lost.
            raise PermissionDenied

    else:  # POST
        is_iframe_target = request.GET.get('iframe', False)
        is_raw = request.GET.get('raw', False)
        need_edit_links = request.GET.get('edit_links', False)
        parent_id = request.POST.get('parent_id', '')

        # Attempt to set a parent
        if show_translation_parent_block and parent_id:
            try:
                parent_doc = get_object_or_404(Document, id=parent_id)
                doc.parent = parent_doc
            except Document.DoesNotExist:
                pass

        # Comparing against localized names for the Save button bothers me, so
        # I embedded a hidden input:
        which_form = request.POST.get('form')

        if which_form == 'doc':
            if doc.allows_editing_by(user):
                post_data = request.POST.copy()

                post_data.update({'locale': document_locale})
                doc_form = DocumentForm(post_data, instance=doc)
                if doc_form.is_valid():
                    # if must be here for section edits
                    if 'slug' in post_data:
                        post_data['slug'] = _join_slug(
                            slug_dict['parent_split'], post_data['slug'])

                    # Get the possibly new slug for the imminent redirection:
                    doc = doc_form.save(None)

                    if is_iframe_target:
                        # TODO: Does this really need to be a template? Just
                        # shoehorning data into a single HTML element.
                        response = HttpResponse("""
                            <span id="iframe-response"
                                  data-status="OK"
                                  data-current-revision="%s">OK</span>
                        """ % doc.current_revision.id)
                        response['X-Frame-Options'] = 'SAMEORIGIN'
                        return response

                    return HttpResponseRedirect(
                        urlparams(reverse('wiki.edit_document',
                                          args=[doc.slug]),
                                  opendescription=1))
                disclose_description = True
            else:
                raise PermissionDenied

        elif which_form == 'rev':
            if not doc.allows_revision_by(user):
                raise PermissionDenied
            else:
                post_data = request.POST.copy()

                rev_form = RevisionForm(post_data,
                                        is_iframe_target=is_iframe_target,
                                        section_id=section_id)
                rev_form.instance.document = doc  # for rev_form.clean()

                # Come up with the original revision to which these changes
                # would be applied.
                orig_rev_id = request.POST.get('current_rev', False)
                if orig_rev_id is False:
                    orig_rev = None
                else:
                    orig_rev = Revision.objects.get(pk=orig_rev_id)
                # Get the document's actual current revision.
                curr_rev = doc.current_revision

                if not rev_form.is_valid():
                    # Was there a mid-air collision?
                    if 'current_rev' in rev_form._errors:
                        # Jump out to a function to escape indentation hell
                        return _edit_document_collision(
                            request, orig_rev, curr_rev, is_iframe_target,
                            is_raw, rev_form, doc_form, section_id,
                            rev, doc)

                if rev_form.is_valid():
                    _save_rev_and_notify(rev_form, request, doc)

                    if is_iframe_target:
                        # TODO: Does this really need to be a template? Just
                        # shoehorning data into a single HTML element.
                        response = HttpResponse("""
                            <span id="iframe-response"
                                  data-status="OK"
                                  data-current-revision="%s">OK</span>
                        """ % doc.current_revision.id)
                        response['X-Frame-Options'] = 'SAMEORIGIN'
                        return response

                    if (is_raw and orig_rev is not None and
                            curr_rev.id != orig_rev.id):
                        # If this is the raw view, and there was an original
                        # revision, but the original revision differed from the
                        # current revision at start of editing, we should tell
                        # the client to refresh the page.
                        response = HttpResponse('RESET')
                        response['X-Frame-Options'] = 'SAMEORIGIN'
                        response.status_code = 205
                        return response

                    if rev_form.instance.is_approved:
                        view = 'wiki.document'
                    else:
                        view = 'wiki.document_revisions'

                    # Construct the redirect URL, adding any needed parameters
                    url = reverse(view, args=[doc.slug], locale=doc.locale)
                    params = {}
                    if is_raw:
                        params['raw'] = 'true'
                        if need_edit_links:
                            # Only need to carry over ?edit_links with ?raw,
                            # because they're on by default in the normal UI
                            params['edit_links'] = 'true'
                        if section_id:
                            # If a section was edited, and we're using the raw
                            # content API, constrain to that section.
                            params['section'] = section_id
                    if params:
                        url = '%s?%s' % (url, urlencode(params))
                    if not is_raw and section_id:
                        # If a section was edited, jump to the section anchor
                        # if we're not getting raw content.
                        url = '%s#%s' % (url, section_id)

                    return HttpResponseRedirect(url)

    parent_path = parent_slug = ''
    if slug_dict['parent']:
        parent_slug = slug_dict['parent']

    if doc.parent_topic_id:
        parent_doc = Document.objects.get(pk=doc.parent_topic_id)
        parent_path = parent_doc.get_absolute_url()
        parent_slug = parent_doc.slug

    attachments = attachments_json(doc.attachments)
    allow_add_attachment = (
        Attachment.objects.allow_add_attachment_by(request.user))

    context = {
        'revision_form': rev_form,
        'document_form': doc_form,
        'section_id': section_id,
        'disclose_description': disclose_description,
        'parent_slug': parent_slug,
        'parent_path': parent_path,
        'revision': rev,
        'document': doc,
        'allow_add_attachment': allow_add_attachment,
        'attachment_form': AttachmentRevisionForm(),
        'attachment_data': attachments,
        'WIKI_DOCUMENT_TAG_SUGGESTIONS': config.WIKI_DOCUMENT_TAG_SUGGESTIONS,
        'attachment_data_json': json.dumps(attachments)
    }
    return render(request, 'wiki/edit_document.html', context)


@xframe_options_sameorigin
def _edit_document_collision(request, orig_rev, curr_rev, is_iframe_target,
                             is_raw, rev_form, doc_form, section_id, rev, doc):
    """Handle when a mid-air collision is detected upon submission"""

    # Process the content as if it were about to be saved, so that the
    # html_diff is close as possible.
    content = (kuma.wiki.content.parse(request.POST['content'])
                                .injectSectionIDs()
                                .serialize())

    # Process the original content for a diff, extracting a section if we're
    # editing one.
    if (doc.is_template):
        curr_content = curr_rev.content
    else:
        tool = kuma.wiki.content.parse(curr_rev.content)
        tool.injectSectionIDs()
        if section_id:
            tool.extractSection(section_id)
        curr_content = tool.serialize()

    if is_raw:
        # When dealing with the raw content API, we need to signal the conflict
        # differently so the client-side can escape out to a conflict
        # resolution UI.
        response = HttpResponse('CONFLICT')
        response.status_code = 409
        return response

    # Make this response iframe-friendly so we can hack around the
    # save-and-edit iframe button
    context = {
        'collision': True,
        'revision_form': rev_form,
        'document_form': doc_form,
        'content': content,
        'current_content': curr_content,
        'section_id': section_id,
        'original_revision': orig_rev,
        'current_revision': curr_rev,
        'revision': rev,
        'document': doc,
    }
    return render(request, 'wiki/edit_document.html', context)


@require_http_methods(['GET', 'POST'])
@permission_required('wiki.move_tree')
@process_document_path
@check_readonly
@prevent_indexing
def move(request, document_slug, document_locale):
    """Move a tree of pages"""
    doc = get_object_or_404(
        Document, locale=document_locale, slug=document_slug)

    descendants = doc.get_descendants()
    slug_split = _split_slug(doc.slug)

    if request.method == 'POST':
        form = TreeMoveForm(initial=request.GET, data=request.POST)
        if form.is_valid():
            conflicts = doc._tree_conflicts(form.cleaned_data['slug'])
            if conflicts:
                return render(request, 'wiki/move_document.html', {
                    'form': form,
                    'document': doc,
                    'descendants': descendants,
                    'descendants_count': len(descendants),
                    'conflicts': conflicts,
                    'SLUG_CLEANSING_REGEX': SLUG_CLEANSING_REGEX,
                })
            move_page.delay(document_locale, document_slug,
                            form.cleaned_data['slug'],
                            request.user.email)
            return render(request, 'wiki/move_requested.html', {
                'form': form,
                'document': doc
            })
    else:
        form = TreeMoveForm()

    return render(request, 'wiki/move_document.html', {
        'form': form,
        'document': doc,
        'descendants': descendants,
        'descendants_count': len(descendants),
        'SLUG_CLEANSING_REGEX': SLUG_CLEANSING_REGEX,
        'specific_slug': slug_split['specific']
    })


@process_document_path
@check_readonly
@superuser_required
def repair_breadcrumbs(request, document_slug, document_locale):
    doc = get_object_or_404(Document,
                            locale=document_locale,
                            slug=document_slug)
    doc.repair_breadcrumbs()
    return redirect(doc.get_absolute_url())


def ckeditor_config(request):
    """Return ckeditor config from database"""
    default_config = EditorToolbar.objects.filter(name='default')
    if default_config.exists():
        code = default_config[0].code
    else:
        code = ''

    context = {
        'editor_config': code,
        'redirect_pattern': REDIRECT_CONTENT,
        'allowed_tags': ' '.join(ALLOWED_TAGS),
    }
    return render(request, 'wiki/ckeditor_config.js', context,
                  content_type="application/x-javascript")


@login_required
@require_POST
def preview_revision(request):
    """
    Create an HTML fragment preview of the posted wiki syntax.
    """
    wiki_content = request.POST.get('content', '')
    kumascript_errors = []
    doc_id = request.POST.get('doc_id')
    if doc_id:
        doc = Document.objects.get(id=doc_id)
    else:
        doc = None

    if kumascript.should_use_rendered(doc, request.GET, html=wiki_content):
        wiki_content, kumascript_errors = kumascript.post(request,
                                                          wiki_content,
                                                          request.locale)
    # TODO: Get doc ID from JSON.
    context = {
        'content': wiki_content,
        'title': request.POST.get('title', ''),
        'kumascript_errors': kumascript_errors,
    }
    return render(request, 'wiki/preview.html', context)


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


@require_GET
@allow_CORS_GET
@process_document_path
def get_children(request, document_slug, document_locale):
    """Retrieves a document and returns its children in a JSON structure"""
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
    except Document.DoesNotExist:
        result = {'error': 'Document does not exist.'}

    result = json.dumps(result)
    return HttpResponse(result, content_type='application/json')


@require_GET
@allow_CORS_GET
@newrelic.agent.function_trace()
def autosuggest_documents(request):
    """Returns the closest title matches for front-end autosuggests"""
    partial_title = request.GET.get('term', '')
    locale = request.GET.get('locale', False)
    current_locale = request.GET.get('current_locale', False)
    exclude_current_locale = request.GET.get('exclude_current_locale', False)

    if not partial_title:
        # Only handle actual autosuggest requests, not requests for a
        # memory-busting list of all documents.
        return HttpResponseBadRequest(_lazy('Autosuggest requires a partial title. For a full document index, see the main page.'))

    # Retrieve all documents that aren't redirects or templates
    docs = (Document.objects.extra(select={'length': 'Length(slug)'})
                            .filter(title__icontains=partial_title,
                                    is_template=0,
                                    is_redirect=0)
                            .exclude(slug__icontains='Talk:')  # Remove old talk pages
                            .order_by('title', 'length'))

    # All locales are assumed, unless a specific locale is requested or banned
    if locale:
        docs = docs.filter(locale=locale)
    if current_locale:
        docs = docs.filter(locale=request.locale)
    if exclude_current_locale:
        docs = docs.exclude(locale=request.locale)

    # Generates a list of acceptable docs
    docs_list = []
    for doc in docs:
        data = doc.get_json_data()
        data['label'] += ' [' + doc.locale + ']'
        docs_list.append(data)

    data = json.dumps(docs_list)
    return HttpResponse(data, content_type='application/json')


@require_GET
@process_document_path
@prevent_indexing
def document_revisions(request, document_slug, document_locale):
    """List all the revisions of a given document."""
    locale = request.GET.get('locale', document_locale)
    document = get_object_or_404(Document.objects
                                         .select_related('current_revision'),
                                 locale=locale,
                                 slug=document_slug)
    if document.current_revision is None:
        raise Http404

    def get_previous(revisions):
        for current_revision in revisions:
            for previous_revision in revisions:
                # we filter out all revisions that are not approved
                # as that's the way the get_previous method does it as well
                # also let's skip comparing the same revisions
                if (not previous_revision.is_approved or
                        current_revision.pk == previous_revision.pk):
                    continue
                # we stick to the first revision that we find
                if previous_revision.created < current_revision.created:
                    current_revision.previous_revision = previous_revision
                    break
        return revisions

    per_page = request.GET.get('limit', 10)

    if not request.user.is_authenticated() and per_page == 'all':
        return render(request, '403.html',
                      {'reason': 'revisions_login_required'}, status=403)

    # Grab revisions, but defer summary and content because they can lead to
    # attempts to cache more than memcached allows.
    revisions = MultiQuerySet(
        (Revision.objects.filter(pk=document.current_revision.pk)
                         .prefetch_related('creator', 'document')
                         .transform(get_previous)),
        (Revision.objects.filter(document=document)
                         .order_by('-created', '-id')
                         .exclude(pk=document.current_revision.pk)
                         .prefetch_related('creator', 'document')
                         .transform(get_previous))
    )

    if not revisions.exists():
        raise Http404

    if per_page == 'all':
        page = None
    else:
        try:
            per_page = int(per_page)
        except ValueError:
            per_page = DOCUMENTS_PER_PAGE

        page = paginate(request, revisions, per_page)
        revisions = page.object_list

    context = {
        'revisions': revisions,
        'document': document,
        'page': page,
    }
    return render(request, 'wiki/document_revisions.html', context)


@require_GET
@xframe_options_sameorigin
@process_document_path
@prevent_indexing
def compare_revisions(request, document_slug, document_locale):
    """Compare two wiki document revisions.

    The ids are passed as query string parameters (to and from).

    """
    locale = request.GET.get('locale', document_locale)
    doc = get_object_or_404(Document,
                            locale=locale,
                            slug=document_slug)

    if 'from' not in request.GET or 'to' not in request.GET:
        raise Http404

    try:
        from_id = smart_int(request.GET.get('from'))
        to_id = smart_int(request.GET.get('to'))
    except:
        # Punt any errors in parameter handling to a 404
        raise Http404

    revision_from = get_object_or_404(Revision, id=from_id, document=doc)
    revision_to = get_object_or_404(Revision, id=to_id, document=doc)

    context = {
        'document': doc,
        'revision_from': revision_from,
        'revision_to': revision_to,
    }

    if request.GET.get('raw', False):
        template = 'wiki/includes/revision_diff_table.html'
    else:
        template = 'wiki/compare_revisions.html'

    return render(request, template, context)


@login_required
@process_document_path
def select_locale(request, document_slug, document_locale):
    """Select a locale to translate the document to."""
    doc = get_object_or_404(Document,
                            locale=document_locale,
                            slug=document_slug)
    return render(request, 'wiki/select_locale.html', {'document': doc})


@require_http_methods(['GET', 'POST'])
@login_required
@process_document_path
@check_readonly
@prevent_indexing
@never_cache
def translate(request, document_slug, document_locale, revision_id=None):
    """
    Create a new translation of a wiki document.

    * document_slug is for the default locale
    * translation is to the request locale

    """
    # TODO: Refactor this view into two views? (new, edit)
    # That might help reduce the headache-inducing branchiness.
    parent_doc = get_object_or_404(Document,
                                   locale=settings.WIKI_DEFAULT_LANGUAGE,
                                   slug=document_slug)
    user = request.user

    if not revision_id:
        # HACK: Seems weird, but sticking the translate-to locale in a query
        # param is the best way to avoid the MindTouch-legacy locale
        # redirection logic.
        document_locale = request.GET.get('tolocale',
                                          document_locale)

    # Set a "Discard Changes" page
    discard_href = ''

    if settings.WIKI_DEFAULT_LANGUAGE == document_locale:
        # Don't translate to the default language.
        return HttpResponseRedirect(reverse(
            'wiki.edit_document', locale=settings.WIKI_DEFAULT_LANGUAGE,
            args=[parent_doc.slug]))

    if not parent_doc.is_localizable:
        message = _lazy(u'You cannot translate this document.')
        context = {'message': message}
        return render(request, 'handlers/400.html', context, status=400)

    if revision_id:
        get_object_or_404(Revision, pk=revision_id)

    based_on_rev = parent_doc.current_or_latest_revision()

    disclose_description = bool(request.GET.get('opendescription'))

    try:
        doc = parent_doc.translations.get(locale=document_locale)
        slug_dict = _split_slug(doc.slug)
    except Document.DoesNotExist:
        doc = None
        disclose_description = True
        slug_dict = _split_slug(document_slug)

        # Find the "real" parent topic, which is its translation
        try:
            parent_topic_translated_doc = (
                parent_doc.parent_topic.translations.get(
                    locale=document_locale))
            slug_dict = _split_slug(
                parent_topic_translated_doc.slug + '/' + slug_dict['specific'])
        except:
            pass

    user_has_doc_perm = ((not doc) or (doc and doc.allows_editing_by(user)))
    user_has_rev_perm = ((not doc) or (doc and doc.allows_revision_by(user)))
    if not user_has_doc_perm and not user_has_rev_perm:
        # User has no perms, bye.
        raise PermissionDenied

    doc_form = rev_form = None

    if user_has_doc_perm:
        if doc:
            # If there's an existing doc, populate form from it.
            discard_href = doc.get_absolute_url()
            doc.slug = slug_dict['specific']
            doc_initial = _document_form_initial(doc)
        else:
            # If no existing doc, bring over the original title and slug.
            discard_href = parent_doc.get_absolute_url()
            doc_initial = {'title': based_on_rev.title,
                           'slug': slug_dict['specific']}
        doc_form = DocumentForm(initial=doc_initial)

    if user_has_rev_perm:
        initial = {'based_on': based_on_rev.id, 'comment': '',
                   'toc_depth': based_on_rev.toc_depth,
                   'localization_tags': ['inprogress']}
        content = None
        if revision_id:
            content = Revision.objects.get(pk=revision_id).content
        elif not doc:
            content = based_on_rev.content
        if content:
            initial.update(content=kuma.wiki.content.parse(content)
                                                    .filterEditorSafety()
                                                    .serialize())
        instance = doc and doc.current_or_latest_revision()
        rev_form = RevisionForm(instance=instance, initial=initial)

    if request.method == 'POST':
        which_form = request.POST.get('form', 'both')
        doc_form_invalid = False

        # Grab the posted slug value in case it's invalid
        posted_slug = request.POST.get('slug', slug_dict['specific'])
        destination_slug = _join_slug(slug_dict['parent_split'], posted_slug)

        if user_has_doc_perm and which_form in ['doc', 'both']:
            disclose_description = True
            post_data = request.POST.copy()

            post_data.update({'locale': document_locale})
            post_data.update({'slug': destination_slug})

            doc_form = DocumentForm(post_data, instance=doc)
            doc_form.instance.locale = document_locale
            doc_form.instance.parent = parent_doc
            if which_form == 'both':
                # Sending a new copy of post so the slug change above
                # doesn't cause problems during validation
                rev_form = RevisionValidationForm(request.POST.copy())
                rev_form.parent_slug = slug_dict['parent']

            # If we are submitting the whole form, we need to check that
            # the Revision is valid before saving the Document.
            if doc_form.is_valid() and (which_form == 'doc' or
                                        rev_form.is_valid()):
                rev_form = RevisionForm(post_data)

                if rev_form.is_valid():
                    doc = doc_form.save(parent_doc)

                    if which_form == 'doc':
                        url = urlparams(reverse('wiki.edit_document',
                                                args=[doc.slug],
                                                locale=doc.locale),
                                        opendescription=1)
                        return HttpResponseRedirect(url)
                else:
                    doc_form.data['slug'] = posted_slug
                    doc_form_invalid = True
            else:
                doc_form.data['slug'] = posted_slug
                doc_form_invalid = True

        if doc and user_has_rev_perm and which_form in ['rev', 'both']:
            post_data = request.POST.copy()
            if 'slug' not in post_data:
                post_data['slug'] = posted_slug

            rev_form = RevisionValidationForm(post_data)
            rev_form.parent_slug = slug_dict['parent']
            rev_form.instance.document = doc  # for rev_form.clean()

            if rev_form.is_valid() and not doc_form_invalid:
                # append final slug
                post_data['slug'] = destination_slug

                # update the post data with the toc_depth of original
                post_data['toc_depth'] = based_on_rev.toc_depth

                rev_form = RevisionForm(post_data)
                rev_form.instance.document = doc  # for rev_form.clean()

                if rev_form.is_valid():
                    parent_id = request.POST.get('parent_id', '')

                    # Attempt to set a parent
                    if parent_id:
                        try:
                            parent_doc = get_object_or_404(Document,
                                                           id=parent_id)
                            rev_form.instance.document.parent = parent_doc
                            doc.parent = parent_doc
                            rev_form.instance.based_on.document = doc.original
                        except Document.DoesNotExist:
                            pass

                    _save_rev_and_notify(rev_form, request, doc)
                    url = reverse('wiki.document', args=[doc.slug],
                                  locale=doc.locale)
                    return HttpResponseRedirect(url)

    if doc:
        from_id = smart_int(request.GET.get('from'), None)
        to_id = smart_int(request.GET.get('to'), None)

        revision_from = get_object_or_none(Revision,
                                           pk=from_id,
                                           document=doc.parent)
        revision_to = get_object_or_none(Revision,
                                         pk=to_id,
                                         document=doc.parent)
    else:
        revision_from = revision_to = None

    parent_split = _split_slug(parent_doc.slug)
    allow_add_attachment = (
        Attachment.objects.allow_add_attachment_by(request.user))

    attachments = []
    if doc and doc.attachments:
        attachments = attachments_json(doc.attachments)

    context = {
        'parent': parent_doc,
        'document': doc,
        'document_form': doc_form,
        'revision_form': rev_form,
        'locale': document_locale,
        'based_on': based_on_rev,
        'disclose_description': disclose_description,
        'discard_href': discard_href,
        'allow_add_attachment': allow_add_attachment,
        'attachment_form': AttachmentRevisionForm(),
        'attachment_data': attachments,
        'attachment_data_json': json.dumps(attachments),
        'WIKI_DOCUMENT_TAG_SUGGESTIONS': config.WIKI_DOCUMENT_TAG_SUGGESTIONS,
        'specific_slug': parent_split['specific'],
        'parent_slug': parent_split['parent'],
        'revision_from': revision_from,
        'revision_to': revision_to,
    }
    return render(request, 'wiki/translate.html', context)


@require_POST
@login_required
@process_document_path
def subscribe_document(request, document_slug, document_locale):
    """Stop watching a document for edits."""
    document = get_object_or_404(
        Document, locale=document_locale, slug=document_slug)
    status = 0

    if EditDocumentEvent.is_notifying(request.user, document):
        EditDocumentEvent.stop_notifying(request.user, document)
    else:
        EditDocumentEvent.notify(request.user, document)
        status = 1

    if request.is_ajax():
        return HttpResponse(json.dumps({'status': status}))

    return HttpResponseRedirect(document.get_absolute_url())


@require_GET
@allow_CORS_GET
@process_document_path
@prevent_indexing
def json_view(request, document_slug=None, document_locale=None):
    """Return some basic document info in a JSON blob."""
    kwargs = {'locale': request.locale, 'current_revision__isnull': False}
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

    json_obj = document.get_json_data(stale=stale)

    data = json.dumps(json_obj)
    return HttpResponse(data, content_type='application/json')


@require_GET
@allow_CORS_GET
@process_document_path
@prevent_indexing
def styles_view(request, document_slug=None, document_locale=None):
    """Return some basic document info in a JSON blob."""
    kwargs = {'slug': document_slug, 'locale': document_locale}
    document = get_object_or_404(Document, **kwargs)
    zone = get_object_or_404(DocumentZone, document=document)
    return HttpResponse(zone.styles, content_type='text/css')


@require_GET
@allow_CORS_GET
@process_document_path
@prevent_indexing
def toc_view(request, document_slug=None, document_locale=None):
    """Return some basic document info in a JSON blob."""
    kwargs = {'locale': request.locale, 'current_revision__isnull': False}
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
    toc_html = document.get_toc_html()
    if toc_html:
        toc_html = '<ol>' + toc_html + '</ol>'

    return HttpResponse(toc_html)


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


@require_POST
def helpful_vote(request, document_path):
    """Vote for Helpful/Not Helpful document"""
    document_locale, document_slug, needs_redirect = (
        locale_and_slug_from_path(document_path, request))

    document = get_object_or_404(
        Document, locale=document_locale, slug=document_slug)

    if not document.has_voted(request):
        ua = request.META.get('HTTP_USER_AGENT', '')[:1000]  # 1000 max_length
        vote = HelpfulVote(document=document, user_agent=ua)

        if 'helpful' in request.POST:
            vote.helpful = True
            message = _('Glad to hear it &mdash; thanks for the feedback!')
        else:
            message = _('Sorry to hear that. Perhaps one of the solutions '
                        'below can help.')

        if request.user.is_authenticated():
            vote.creator = request.user
        else:
            vote.anonymous_id = request.anonymous.anonymous_id

        vote.save()
    else:
        message = _('You already voted on this Article.')

    if request.is_ajax():
        return HttpResponse(json.dumps({'message': message}))

    return HttpResponseRedirect(document.get_absolute_url())


def _check_doc_revision_for_alteration(request, document_path, revision_id):
    document_locale, document_slug, needs_redirect = (
        locale_and_slug_from_path(document_path, request))

    revision = get_object_or_404(Revision, pk=revision_id,
                                 document__slug=document_slug)
    document = revision.document

    if not document.allows_revision_by(request.user):
        raise PermissionDenied

    return document, revision


@login_required
@check_readonly
def revert_document(request, document_path, revision_id):
    """Revert document to a specific revision."""
    document, revision = _check_doc_revision_for_alteration(request,
                                                            document_path,
                                                            revision_id)
    if request.method == 'GET':
        # Render the confirmation page
        return render(request, 'wiki/confirm_revision_revert.html',
                      {'revision': revision, 'document': document})

    document.revert(revision, request.user, request.POST.get('comment'))
    return HttpResponseRedirect(reverse('wiki.document_revisions',
                                args=[document.slug]))


@login_required
@permission_required('wiki.delete_revision')
@check_readonly
def delete_revision(request, document_path, revision_id):
    """Delete a revision."""
    document, revision = _check_doc_revision_for_alteration(request,
                                                            document_path,
                                                            revision_id)
    if request.method == 'GET':
        # Render the confirmation page
        return render(request, 'wiki/confirm_revision_delete.html',
                      {'revision': revision, 'document': document})

    # Handle confirm delete form POST
    log.warning('User %s is deleting revision with id=%s' %
                (request.user, revision.id))
    Revision.objects.filter(based_on=revision).update(based_on=None)

    if document.current_revision == revision:
        # If the current_revision is being deleted, lets try to update it to
        # the previous approved revision.
        revs = document.revisions.filter(
            is_approved=True).order_by('-created')

        # Using len() here instead of count(), because count is affected by
        # a cache delay of 60 seconds, so if the revisions are deleted in
        # a short time span, the value returned by count() doesn't
        # correspond to the number of existing reviews
        if len(revs) > 1:
            rev = revs[1]
            rev.make_current()
        else:
            # The document is deleted along with its last revision
            document.delete()
            return redirect('wiki.all_documents')

    revision.delete()

    return HttpResponseRedirect(reverse('wiki.document_revisions',
                                        args=[document.slug]))


@login_required
@permission_required('wiki.delete_document')
@check_readonly
@process_document_path
def delete_document(request, document_slug, document_locale):
    """
    Delete a Document.
    """
    document = get_object_or_404(Document,
                                 locale=document_locale,
                                 slug=document_slug)

    # HACK: https://bugzil.la/972545 - Don't delete pages that have children
    # TODO: https://bugzil.la/972541 -  Deleting a page that has subpages
    prevent = document.children.exists()

    first_revision = document.revisions.all()[0]

    if request.method == 'POST':
        form = DocumentDeletionForm(data=request.POST)
        if form.is_valid():
            DocumentDeletionLog.objects.create(
                locale=document.locale,
                slug=document.slug,
                user=request.user,
                reason=form.cleaned_data['reason']
            )
            document.delete()
            return HttpResponseRedirect(document.get_absolute_url())
    else:
        form = DocumentDeletionForm()
    return render(request,
                  'wiki/confirm_document_delete.html',
                  {'document': document, 'form': form, 'request': request,
                   'revision': first_revision, 'prevent': prevent})


@login_required
@permission_required('wiki.restore_document')
@check_readonly
@process_document_path
def restore_document(request, document_slug, document_locale):
    """
    Restore a deleted Document.

    """
    document = get_object_or_404(Document.deleted_objects.all(),
                                 slug=document_slug,
                                 locale=document_locale)
    document.undelete()
    return redirect(document.get_absolute_url())


@login_required
@permission_required('wiki.purge_document')
@check_readonly
@process_document_path
def purge_document(request, document_slug, document_locale):
    """
    Permanently purge a deleted Document.

    """
    document = get_object_or_404(Document.deleted_objects.all(),
                                 slug=document_slug,
                                 locale=document_locale)
    if request.method == 'POST' and \
       'confirm' in request.POST:
        document.purge()
        return redirect(reverse('wiki.document',
                                args=(document_slug,),
                                locale=document_locale))
    else:
        return render(request,
                      'wiki/confirm_purge.html',
                      {'document': document})


@login_required
@require_POST
@process_document_path
def quick_review(request, document_slug, document_locale):
    """
    Quickly mark a revision as no longer needing a particular type
    of review."""
    doc = get_object_or_404(Document,
                            locale=document_locale,
                            slug=document_slug)

    if not doc.allows_revision_by(request.user):
        raise PermissionDenied

    rev_id = request.POST.get('revision_id')
    if not rev_id:
        raise Http404

    rev = get_object_or_404(Revision, pk=rev_id)

    if rev.id != doc.current_revision.id:
        # TODO: Find a better way to bail out of a collision.
        # Ideal is to kick them to the diff view, but that expects
        # fully-filled-out editing forms, and we don't have those
        # here.
        raise PermissionDenied(_lazy("Document has been edited; please re-review."))

    needs_technical = rev.needs_technical_review
    needs_editorial = rev.needs_editorial_review

    if not any((needs_technical, needs_editorial)):
        # No need to "approve" something that doesn't need it.
        return redirect(doc)

    approve_technical = request.POST.get('approve_technical', False)
    approve_editorial = request.POST.get('approve_editorial', False)

    new_tags = []
    messages = []

    if needs_technical and not approve_technical:
        new_tags.append('technical')
    elif needs_technical:
        messages.append('Technical review completed.')

    if needs_editorial and not approve_editorial:
        new_tags.append('editorial')
    elif needs_editorial:
        messages.append('Editorial review completed.')

    if messages:
        # We approved something, make the new revision.
        new_rev = doc.revise(request.user,
                             data={'summary': ' '.join(messages), 'comment': ' '.join(messages)})
        if new_tags:
            new_rev.review_tags.set(*new_tags)
        else:
            new_rev.review_tags.clear()
    return redirect(doc)


def _document_form_initial(document):
    """Return a dict with the document data pertinent for the form."""
    return {
        'title': document.title,
        'slug': document.slug,
        'category': document.category,
        'is_localizable': document.is_localizable,
        'tags': list(document.tags.values_list('name', flat=True))
    }


def _save_rev_and_notify(rev_form, request, document):
    """Save the given RevisionForm and send notifications."""
    creator = request.user
    # have to check for first edit before we rev_form.save
    first_edit = creator.profile.wiki_activity().count() == 0

    new_rev = rev_form.save(creator, document)

    if waffle.switch_is_active('store_revision_ips'):
        RevisionIP(revision=new_rev, ip=get_ip(request)).save()

    if first_edit:
        send_first_edit_email.delay(new_rev.pk)

    document.schedule_rendering('max-age=0')

    # Enqueue notifications
    EditDocumentEvent(new_rev).fire(exclude=new_rev.creator)


# Legacy MindTouch redirects.

MINDTOUCH_NAMESPACES = (
    'Help',
    'Help_talk',
    'Project',
    'Project_talk',
    'Special',
    'Talk',
    'Template',
    'Template_talk',
    'User',
)

MINDTOUCH_PROBLEM_LOCALES = {
    'cn': 'zh-CN',
    'en': 'en-US',
    'zh_cn': 'zh-CN',
    'zh_tw': 'zh-TW',
}


def mindtouch_namespace_redirect(request, namespace, slug):
    """
    For URLs in special namespaces (like Talk:, User:, etc.), redirect
    if possible to the appropriate new URL in the appropriate
    locale. If the locale cannot be correctly determined, fall back to
    en-US.
    """
    new_locale = new_slug = None
    if namespace in ('Talk', 'Project', 'Project_talk'):
        # These namespaces carry the old locale in their URL, which
        # simplifies figuring out where to send them.
        locale, _, doc_slug = slug.partition('/')
        new_locale = settings.MT_TO_KUMA_LOCALE_MAP.get(locale, 'en-US')
        new_slug = '%s:%s' % (namespace, doc_slug)
    elif namespace == 'User':
        # For users, we look up the latest revision and get the locale
        # from there.
        new_slug = '%s:%s' % (namespace, slug)
        try:
            rev = (Revision.objects.filter(document__slug=new_slug)
                                   .latest('created'))
            new_locale = rev.document.locale
        except Revision.DoesNotExist:
            # If that doesn't work, bail out to en-US.
            new_locale = 'en-US'
    else:
        # Templates, etc. don't actually have a locale, so we give
        # them the default.
        new_locale = 'en-US'
        new_slug = '%s:%s' % (namespace, slug)
    if new_locale:
        new_url = '/%s/docs/%s' % (request.locale, new_slug)
    return HttpResponsePermanentRedirect(new_url)


def mindtouch_to_kuma_redirect(request, path):
    """
    Given a request to a Mindtouch-generated URL, generate a redirect
    to the correct corresponding kuma URL.
    """
    new_locale = None
    if path.startswith('Template:MindTouch'):
        # MindTouch's default templates. There shouldn't be links to
        # them anywhere in the wild, but just in case we 404 them.
        raise Http404
    if path.endswith('/'):
        # If there's a trailing slash, snip it off.
        path = path[:-1]
    if ':' in path:
        namespace, _, slug = path.partition(':')
        # The namespaces (Talk:, User:, etc.) get their own
        # special-case handling.
        if namespace in MINDTOUCH_NAMESPACES:
            return mindtouch_namespace_redirect(request, namespace, slug)
    if '/' in path:
        maybe_locale, _, slug = path.partition('/')
        # There are three problematic locales that MindTouch had which
        # can still be in the path we see after the locale
        # middleware's done its bit. Since those are easy, we check
        # them first.
        if maybe_locale in MINDTOUCH_PROBLEM_LOCALES:
            new_locale = MINDTOUCH_PROBLEM_LOCALES[maybe_locale]
            # We do not preserve UI locale here -- these locales won't
            # be picked up correctly by the locale middleware, and
            # anyone trying to view the document in its locale with
            # their own UI locale will have the correct starting URL
            # anyway.
            new_url = '/%s/docs/%s' % (new_locale, slug)
            if 'view' in request.GET:
                new_url = '%s$%s' % (new_url, request.GET['view'])
            return HttpResponsePermanentRedirect(new_url)
        # Next we try looking up a Document with the possible locale
        # we've pulled out.
        try:
            doc = Document.objects.get(slug=slug, locale=maybe_locale)
        except Document.DoesNotExist:
            pass
    # Last attempt: we try the request locale as the document locale,
    # and see if that matches something.
    try:
        doc = Document.objects.get(slug=path, locale=request.locale)
    except Document.DoesNotExist:
        raise Http404
    location = doc.get_absolute_url()
    if 'view' in request.GET:
        location = '%s$%s' % (location, request.GET['view'])
    return HttpResponsePermanentRedirect(location)


@user_passes_test(lambda u: u.is_superuser)
def load_documents(request):
    """Load documents from uploaded file."""
    form = ImportForm()
    if request.method == 'POST':

        # Accept the uploaded document data.
        file_data = None
        form = ImportForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']
            if uploaded_file.multiple_chunks():
                file_data = open(uploaded_file.temporary_file_path(), 'r')
            else:
                file_data = uploaded_file.read()

        if file_data:
            # Try to import the data, but report any error that occurs.
            try:
                counter = Document.objects.load_json(request.user, file_data)
                user_msg = (_('%(obj_count)d object(s) loaded.') %
                            {'obj_count': counter, })
                messages.add_message(request, messages.INFO, user_msg)
            except Exception, e:
                err_msg = (_('Failed to import data: %(error)s') %
                           {'error': '%s' % e, })
                messages.add_message(request, messages.ERROR, err_msg)

    context = {'import_file_form': form, }
    return render(request, 'admin/wiki/document/load_data_form.html', context)


@xframe_options_sameorigin
@process_document_path
def flag(request, document_slug, document_locale):
    doc = get_object_or_404(Document,
                            slug=document_slug,
                            locale=document_locale)

    if request.method == 'POST':
        form = DocumentContentFlagForm(data=request.POST)
        if form.is_valid():
            flag_type = form.cleaned_data['flag_type']
            recipients = None
            if (flag_type in FLAG_NOTIFICATIONS and
                    FLAG_NOTIFICATIONS[flag_type]):
                query = Q(user__email__isnull=True) | Q(user__email='')
                recipients = (UserProfile.objects.exclude(query)
                                                 .values_list('user__email',
                                                              flat=True))
                recipients = list(recipients)

            flag, created = ContentFlag.objects.flag(
                request=request, object=doc,
                flag_type=flag_type,
                explanation=form.cleaned_data['explanation'],
                recipients=recipients)
            return HttpResponseRedirect(reverse(
                'wiki.document', locale=document_locale,
                args=[document_slug]))
    else:
        form = DocumentContentFlagForm(data=request.GET)

    return render(request, 'wiki/flag.html', {'form': form, 'doc': doc})
