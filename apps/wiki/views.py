# coding=utf-8

from datetime import datetime
import time
import json
from collections import defaultdict
import base64
import httplib
import hashlib
import logging
from urllib import urlencode
from string import ascii_letters

import requests
import bleach

try:
    from functools import wraps
except ImportError:
    from django.utils.functional import wraps

from django.conf import settings
from django.db import transaction
from django.core.exceptions import PermissionDenied
from django.template import RequestContext
from django.core.cache import cache
from django.contrib import messages
from django.http import (HttpResponse, HttpResponseRedirect,
                         HttpResponsePermanentRedirect,
                         Http404, HttpResponseBadRequest)
from django.shortcuts import get_object_or_404, render_to_response, redirect
from django.views.decorators.http import (require_GET, require_POST,
                                          require_http_methods, condition)

import constance.config

from waffle.decorators import waffle_flag
from waffle import flag_is_active

import jingo
from tower import ugettext_lazy as _lazy
from tower import ugettext as _

from smuggler.utils import superuser_required
from smuggler.forms import ImportFileForm

from access.decorators import permission_required, login_required
from sumo.helpers import urlparams
from sumo.urlresolvers import Prefixer, reverse
from sumo.utils import paginate, smart_int
from wiki import (DOCUMENTS_PER_PAGE, TEMPLATE_TITLE_PREFIX, ReadOnlyException)
from wiki.decorators import check_readonly
from wiki.events import (EditDocumentEvent, ReviewableRevisionInLocaleEvent,
                         ApproveRevisionInLocaleEvent)
from wiki.forms import (DocumentForm, RevisionForm, ReviewForm, RevisionValidationForm,
                        AttachmentRevisionForm)
from wiki.models import (Document, Revision, HelpfulVote, EditorToolbar,
                         DocumentTag, ReviewTag, Attachment,
                         DocumentRenderingInProgress,
                         DocumentRenderedContentNotAvailable,
                         CATEGORIES,
                         OPERATING_SYSTEMS, GROUPED_OPERATING_SYSTEMS,
                         FIREFOX_VERSIONS, GROUPED_FIREFOX_VERSIONS,
                         REVIEW_FLAG_TAGS_DEFAULT, ALLOWED_ATTRIBUTES,
                         ALLOWED_TAGS, ALLOWED_STYLES,
                         DOCUMENT_LAST_MODIFIED_CACHE_KEY_TMPL,
                         get_current_or_latest_revision)
from wiki.tasks import send_reviewed_notification, schedule_rebuild_kb
import wiki.content
from wiki import kumascript

from pyquery import PyQuery as pq
from django.utils.safestring import mark_safe

import logging

log = logging.getLogger('k.wiki')


OS_ABBR_JSON = json.dumps(dict([(o.slug, True)
                                for o in OPERATING_SYSTEMS]))
BROWSER_ABBR_JSON = json.dumps(dict([(v.slug, v.show_in_ui)
                                     for v in FIREFOX_VERSIONS]))


def _version_groups(versions):
    """Group versions so browser+version pairs can be mapped to {for} slugs.

    See test_version_groups for an example.

    """
    def split_slug(slug):
        """Given something like fx35, split it into an alphabetic prefix and a
        suffix, returning a 2-tuple like ('fx', '35')."""
        right = slug.lstrip(ascii_letters)
        left_len = len(slug) - len(right)
        return slug[:left_len], slug[left_len:]

    slug_groups = {}
    for v in versions:
        left, right = split_slug(v.slug)
        slug_groups.setdefault(left, []).append((v.max_version, right))
    for g in slug_groups.itervalues():
        g.sort()
    return slug_groups


VERSION_GROUP_JSON = json.dumps(_version_groups(FIREFOX_VERSIONS))

SHOWFOR_DATA = {
    'oses': GROUPED_OPERATING_SYSTEMS,
    'oses_json': OS_ABBR_JSON,
    'browsers': GROUPED_FIREFOX_VERSIONS,
    'browsers_json': BROWSER_ABBR_JSON,
    'version_group_json': VERSION_GROUP_JSON,
}


def process_document_path(func, reverse_name='wiki.document'):
    """Decorator to process document_path into locale and slug, with
    auto-redirect if necessary."""

    # This function takes generic args and kwargs so it can presume as little
    # as possible on the view method signature.
    @wraps(func)
    def process(request, document_path=None, *args, **kwargs):

        if kwargs.get('bypass_process_document_path', False):
            # Support an option to bypass this decorator altogether, so one
            # view can directly call another view.
            del kwargs['bypass_process_document_path']
            return func(request, document_path, *args, **kwargs)

        document_slug, document_locale = None, None
        if document_path:

            # Parse the document path into locale and slug.
            document_locale, document_slug, needs_redirect = (Document
                    .locale_and_slug_from_path(document_path, request))

            # Add check for "local" URL, remove trailing slash
            slug_length = len(document_slug)
            if slug_length and document_slug[slug_length - 1] == '/':
                needs_redirect = True
                document_slug = document_slug.rstrip('/')

            if not document_slug:
                # If there's no slug, then this is just a 404.
                raise Http404()

            if request.GET.get('raw', False) is not False:
                # HACK: There are and will be a lot of kumascript templates
                # based on legacy DekiScript which will attempt to request
                # old-style URLs. Skip 301 redirects for raw content.
                needs_redirect = False

            if needs_redirect:
                # This catches old MindTouch locales, missing locale, and a few
                # other cases to fire off a 301 Moved permanent redirect.
                url = reverse('wiki.document', locale=document_locale,
                              args=[document_slug])
                url = urlparams(url, query_dict=request.GET)
                return HttpResponsePermanentRedirect(url)

        # Set the kwargs that decorated methods will expect.
        kwargs['document_slug'] = document_slug
        kwargs['document_locale'] = document_locale
        return func(request, *args, **kwargs)

    return process


def _document_last_modified(request, document_slug, document_locale):
    """Utility function to derive the last modified timestamp of a document.
    Mainly for the @condition decorator."""
    nk = u'/'.join((document_locale, document_slug))
    nk_hash = hashlib.md5(nk.encode('utf8')).hexdigest()
    cache_key = DOCUMENT_LAST_MODIFIED_CACHE_KEY_TMPL % nk_hash
    try:
        last_mod = cache.get(cache_key)
        if not last_mod:
            doc = Document.objects.get(locale=document_locale,
                                       slug=document_slug)

            # Convert python datetime to Unix epoch seconds. This is more
            # easily digested by the cache, and is more compatible with other
            # services that might spy on Kuma's cache entries (eg. KumaScript)
            last_mod = doc.modified.strftime('%s')
            cache.set(cache_key, last_mod)

        # Convert the cached Unix epoch seconds back to Python datetime
        return datetime.fromtimestamp(float(last_mod))

    except Document.DoesNotExist:
        return None


def prevent_indexing(func):
    """Decorator to prevent a page from being indexable by robots"""
    @wraps(func)
    def _added_header(request, *args, **kwargs):
        response = func(request, *args, **kwargs)
        response['X-Robots-Tag'] = 'noindex'
        return response
    return _added_header


def _format_attachment_obj(attachments):
    attachments_list = []
    for attachment in attachments:
        html = jingo.get_env().select_template(['wiki/includes/attachment_row.html'])
        obj = {
            'title': attachment.title,
            'date': str(attachment.current_revision.created),
            'description': attachment.current_revision.description,
            'url': attachment.get_file_url(),
            'size': attachment.current_revision.file.size,
            'creator': attachment.current_revision.creator.username,
            'creatorUrl': reverse('devmo.views.profile_view', 
                            args=[attachment.current_revision.creator]),
            'revision': attachment.current_revision.id,
            'id': attachment.id,
            'mime': attachment.current_revision.mime_type
        }
        obj['html'] = mark_safe(html.render({ 'attachment': obj }))
        attachments_list.append(obj)
    return attachments_list



def _split_slug(slug):
    """Utility function to do basic slug splitting"""
    slug_split = slug.split('/')
    length = len(slug_split)
    root = None
    if length > 1:
        root = slug_split[0]
    specific = slug_split.pop()

    return {'specific': specific, 'parent': '/'.join(slug_split),
            'full': slug, 'parent_split': slug_split, 'length': length,
            'root': root}


def _join_slug(parent_split, slug):
    parent_split.append(slug)
    return '/'.join(parent_split)


def get_seo_description(content):
    # Create an SEO summary
    # TODO:  Google only takes the first 180 characters, so maybe we find a logical
    #        way to find the end of sentence before 180?
    seo_summary = ''
    try:
        if content:
            # Need to add a BR to the page content otherwise pyQuery wont find a 
            # <p></p> element if it's the only element in the doc_html
            seo_analyze_doc_html = content + '<br />'
            page = pq(seo_analyze_doc_html)

            # Look for the SEO summary class first
            summaryClasses = page.find('.seoSummary')
            if len(summaryClasses):
                seo_summary = summaryClasses.text()
            else:
                paragraphs = page.find('p')
                if paragraphs.length:
                    for p in range(len(paragraphs)):
                        item = paragraphs.eq(p)
                        text = item.text()
                        # Checking for a parent length of 2 
                        # because we don't want p's wrapped
                        # in DIVs ("<div class='warning'>") and pyQuery adds 
                        # "<html><div>" wrapping to entire document
                        if (len(text) and 
                            not 'Redirect' in text and 
                            text.find(u'«') == -1 and
                            text.find('&laquo') == -1 and
                            item.parents().length == 2):
                            seo_summary = text.strip()
                            break
    except:
        logging.debug('Could not create SEO summary');

    # Post-found cleanup
    seo_summary = seo_summary.replace('<', '').replace('>', '')

    return seo_summary


@require_http_methods(['GET', 'HEAD'])
@process_document_path
@condition(last_modified_func=_document_last_modified)
@transaction.autocommit  # For rendering bookkeeping, needs immediate updates
def document(request, document_slug, document_locale):
    """View a wiki document."""
    fallback_reason = None
    base_url = request.build_absolute_uri('/')
    slug_dict = _split_slug(document_slug)

    # If a slug isn't available in the requested locale, fall back to en-US:
    try:
        doc = Document.objects.get(locale=document_locale, slug=document_slug)
        if (not doc.current_revision and doc.parent and
            doc.parent.current_revision):
            # This is a translation but its current_revision is None
            # and OK to fall back to parent (parent is approved).
            fallback_reason = 'translation_not_approved'
        elif not doc.current_revision:
            # No current_revision, no parent with current revision, so
            # nothing to show.
            fallback_reason = 'no_content'

    except Document.DoesNotExist:

        # We can throw a 404 immediately if the request type is HEAD
        if request.method == 'HEAD':
            raise Http404

        try:
            # Look in default language:
            doc = Document.objects.get(locale=settings.WIKI_DEFAULT_LANGUAGE,
                                       slug=document_slug)

            # If there's a translation to the requested locale, take it:
            translation = doc.translated_to(document_locale)
            if translation and translation.current_revision:
                url = translation.get_absolute_url()
                url = urlparams(url, query_dict=request.GET)
                return HttpResponseRedirect(url)
            elif translation and doc.current_revision:
                # Found a translation but its current_revision is None
                # and OK to fall back to parent (parent is approved).
                fallback_reason = 'translation_not_approved'
            elif doc.current_revision:
                # There is no translation
                # and OK to fall back to parent (parent is approved).
                fallback_reason = 'no_translation'

        except Document.DoesNotExist:

            # If any of these parameters are present, throw a real 404.
            if (request.GET.get('raw', False) is not False or
                request.GET.get('include', False) is not False or
                request.GET.get('nocreate', False) is not False):
                raise Http404

            # The user may be trying to create a child page; if a parent exists
            # for this document, redirect them to the "Create" page
            # Otherwise, they could be trying to create a main level doc
            url = reverse('wiki.new_document', locale=document_locale)

            if slug_dict['length'] > 1:
                try:
                    parent_doc = Document.objects.get(locale=document_locale,
                                                      slug=slug_dict['parent'],
                                                      is_template=0)

                    # Redirect to create page with parent ID
                    url = urlparams(url, parent=parent_doc.id,
                                    slug=slug_dict['specific'])
                    return HttpResponseRedirect(url)
                except Document.DoesNotExist:
                    raise Http404

            # This is a "base level" redirect, i.e. no parent
            url = urlparams(url, slug=document_slug)
            return HttpResponseRedirect(url)

    # Obey explicit redirect pages:
    # Don't redirect on redirect=no (like Wikipedia), so we can link from a
    # redirected-to-page back to a "Redirected from..." link, so you can edit
    # the redirect.
    redirect_url = (None if request.GET.get('redirect') == 'no'
                    else doc.redirect_url())

    if redirect_url:
        url = urlparams(redirect_url, query_dict=request.GET,
                        redirectslug=doc.slug, redirectlocale=doc.locale)
        return HttpResponsePermanentRedirect(url)

    # Get "redirected from" doc if we were redirected:
    redirect_slug = request.GET.get('redirectslug')
    redirect_locale = request.GET.get('redirectlocale')
    redirected_from = None
    if redirect_slug and redirect_locale:
        try:
            redirected_from = Document.objects.get(locale=redirect_locale,
                                                   slug=redirect_slug)
        except Document.DoesNotExist:
            pass

    # Utility to set common headers used by all response exit points
    response_headers = dict()

    def set_common_headers(r):
        if doc.current_revision:
            r['x-kuma-revision'] = doc.current_revision.id
        # Finally, set any extra headers. update() doesn't work here.
        for k, v in response_headers.items():
            r[k] = v
        return r

    # Grab some parameters that affect output
    section_id = request.GET.get('section', None)
    show_raw = request.GET.get('raw', False) is not False
    is_include = request.GET.get('include', False) is not False
    need_edit_links = request.GET.get('edit_links', False) is not False

    render_raw_fallback = False

    # Grab the document HTML as a fallback, then attempt to use kumascript:
    doc_html, ks_errors = doc.html, None
    if kumascript.should_use_rendered(doc, request.GET):

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
            # There was no rendered content available, and we were unable to
            # render it on the spot. So, fall back to presenting raw content
            render_raw_fallback = True

    toc_html = None
    if not doc.is_template:

        doc_html = (wiki.content.parse(doc_html)
                                .injectSectionIDs()
                                .serialize())

        # Start applying some filters to the document HTML
        tool = (wiki.content.parse(doc_html))

        # Generate a TOC for the document using the sections provided by
        # SectionEditingLinks
        if doc.show_toc and not show_raw:
            toc_html = (wiki.content.parse(tool.serialize())
                                    .filter(wiki.content.SectionTOCFilter)
                                    .serialize())

        # If a section ID is specified, extract that section.
        if section_id:
            tool.extractSection(section_id)

        # Annotate links within the page, but only if not sending raw source.
        if not show_raw:
            tool.annotateLinks(base_url=base_url)

        # If this user can edit the document, inject some section editing
        # links.
        if ((need_edit_links or not show_raw) and
                request.user.is_authenticated() and
                doc.allows_revision_by(request.user)):
            tool.injectSectionEditingLinks(doc.full_path, doc.locale)

        doc_html = tool.serialize()

        # If this is an include, filter out the class="noinclude" blocks.
        if is_include:
            doc_html = (wiki.content.filter_out_noinclude(doc_html))

    # if ?raw parameter is supplied, then we respond with raw page source
    # without template wrapping or edit links. This is also permissive for
    # iframe inclusion
    if show_raw:
        response = HttpResponse(doc_html)
        response['x-frame-options'] = 'Allow'
        response['X-Robots-Tag'] = 'noindex'
        if constance.config.KUMA_CUSTOM_CSS_PATH == doc.get_absolute_url():
            response['Content-Type'] = 'text/css; charset=utf-8'
        elif doc.is_template:
            # Treat raw, un-bleached template source as plain text, not HTML.
            response['Content-Type'] = 'text/plain; charset=utf-8'
        return set_common_headers(response)

    related = doc.related_documents.order_by('-related_to__in_common')[0:5]

    # Get the contributors. (To avoid this query, we could render the
    # the contributors right into the Document's html field.)
    # NOTE: .only() avoids a memcache object-too-large error for large wiki
    # pages when an attempt is made to cache all revisions
    contributors = set([r.creator for r in doc.revisions
                                            .filter(is_approved=True)
                                            .only('creator')
                                            .select_related('creator')])
    # TODO: Port this kitsune feature over, eventually:
    #     https://github.com/jsocol/kitsune/commit/
    #       f1ebb241e4b1d746f97686e65f49e478e28d89f2

    # Get the SEO summary
    seo_summary = ''
    if not doc.is_template:
        seo_summary = get_seo_description(doc_html)

    # Get the additional title information, if necessary
    seo_parent_title = ''
    if slug_dict['root']:
        try:
            root_doc = Document.objects.get(locale=document_locale,
                                            slug=slug_dict['root'])
            seo_parent_title = ' - ' + root_doc.title
        except Document.DoesNotExist:
            logging.debug('Root document could not be found')

    # Retrieve file attachments
    attachments = _format_attachment_obj(doc.attachments)
    
    data = {'document': doc, 'document_html': doc_html, 'toc_html': toc_html,
            'redirected_from': redirected_from,
            'related': related, 'contributors': contributors,
            'fallback_reason': fallback_reason,
            'kumascript_errors': ks_errors,
            'render_raw_fallback': render_raw_fallback,
            'seo_summary': seo_summary,
            'seo_parent_title': seo_parent_title,
            'attachment_data': attachments,
            'attachment_data_json': json.dumps(attachments)}
    data.update(SHOWFOR_DATA)

    response = jingo.render(request, 'wiki/document.html', data)
    # FIXME: For some reason, the ETag isn't coming through here.
    return set_common_headers(response)


@prevent_indexing
@process_document_path
def revision(request, document_slug, document_locale, revision_id):
    """View a wiki document revision."""
    rev = get_object_or_404(Revision, pk=revision_id,
                            document__slug=document_slug)
    data = {'document': rev.document, 'revision': rev}
    data.update(SHOWFOR_DATA)
    return jingo.render(request, 'wiki/revision.html', data)


@require_GET
def list_documents(request, category=None, tag=None):
    """List wiki documents."""
    category_id = None
    if category:
        try:
            category_id = int(category)
        except ValueError:
            raise Http404
        try:
            category = unicode(dict(CATEGORIES)[category_id])
        except KeyError:
            raise Http404

    # Taggit offers a slug - but use name here, because the slugification
    # stinks and is hard to customize.
    tag_obj = tag and get_object_or_404(DocumentTag, name=tag) or None
    docs = Document.objects.filter_for_list(locale=request.locale,
                                             category=category_id,
                                             tag=tag_obj)
    docs = paginate(request, docs, per_page=DOCUMENTS_PER_PAGE)
    return jingo.render(request, 'wiki/list_documents.html',
                        {'documents': docs,
                         'category': category,
                         'tag': tag})

@require_GET
def list_templates(request):
    """Returns listing of all templates"""
    docs = Document.objects.filter(is_template=True).order_by('title')
    docs = paginate(request, docs, per_page=DOCUMENTS_PER_PAGE)
    return jingo.render(request, 'wiki/list_documents.html',
                        {'documents': docs,
                         'is_templates': True})


@require_GET
def list_documents_for_review(request, tag=None):
    """Lists wiki documents with revisions flagged for review"""
    tag_obj = tag and get_object_or_404(ReviewTag, name=tag) or None
    docs = paginate(request, Document.objects.filter_for_review(tag=tag_obj),
                    per_page=DOCUMENTS_PER_PAGE)
    return jingo.render(request, 'wiki/list_documents_for_review.html',
                        {'documents': docs,
                         'tag': tag_obj,
                         'tag_name': tag})


@login_required
@check_readonly
@prevent_indexing
@transaction.autocommit  # For rendering bookkeeping, needs immediate updates
def new_document(request):
    """Create a new wiki document."""
    initial_parent_id = request.GET.get('parent', '')
    initial_slug = request.GET.get('slug', '')
    initial_title = initial_slug.replace('_', ' ')

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
            logging.debug('Cannot find parent')

    if request.method == 'GET':

        initial_data = {}

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
            'review_tags': review_tags,
            'show_toc': True
        })

        allow_add_attachment = Attachment.objects.allow_add_attachment_by(request.user)
        return jingo.render(request, 'wiki/new_document.html',
                            {'is_template': is_template,
                             'parent_slug': parent_slug,
                             'parent_id': initial_parent_id,
                             'document_form': doc_form,
                             'revision_form': rev_form,
                             'allow_add_attachment': allow_add_attachment,
                             'attachment_form': AttachmentRevisionForm(),
                             'parent_path': parent_path})

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
            _save_rev_and_notify(rev_form, request.user, doc)
            if doc.current_revision.is_approved:
                view = 'wiki.document'
            else:
                view = 'wiki.document_revisions'
            return HttpResponseRedirect(reverse(view,
                                        args=[doc.full_path]))
        else:
            doc_form.data['slug'] = posted_slug
    else:
        doc_form.data['slug'] = posted_slug

    allow_add_attachment = Attachment.objects.allow_add_attachment_by(request.user)
    return jingo.render(request, 'wiki/new_document.html',
                        {'is_template': is_template,
                         'document_form': doc_form,
                         'revision_form': rev_form,
                         'allow_add_attachment': allow_add_attachment,
                         'attachment_form': AttachmentRevisionForm(),
                         'parent_slug': parent_slug,
                         'parent_path': parent_path})


@require_http_methods(['GET', 'POST'])
@login_required  # TODO: Stop repeating this knowledge here and in
                 # Document.allows_editing_by.
@process_document_path
@check_readonly
@prevent_indexing
@transaction.autocommit  # For rendering bookkeeping, needs immediate updates
def edit_document(request, document_slug, document_locale, revision_id=None):
    """Create a new revision of a wiki document, or edit document metadata."""
    doc = get_object_or_404(
        Document, locale=document_locale, slug=document_slug)
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
                logging.debug('Could not find posted parent')


        # Comparing against localized names for the Save button bothers me, so
        # I embedded a hidden input:
        which_form = request.POST.get('form')

        if which_form == 'doc':
            if doc.allows_editing_by(user):
                post_data = request.POST.copy()

                post_data.update({'locale': document_locale})
                doc_form = DocumentForm(post_data, instance=doc)
                if doc_form.is_valid():

                    if 'slug' in post_data:  # if must be here for section edits
                        post_data['slug'] = _join_slug(slug_dict['parent_split'], post_data['slug'])

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
                        response['x-frame-options'] = 'SAMEORIGIN'
                        return response

                    return HttpResponseRedirect(
                        urlparams(reverse('wiki.edit_document',
                                          args=[doc.full_path]),
                                  opendescription=1))
                disclose_description = True
            else:
                raise PermissionDenied

        elif which_form == 'rev':
            if not doc.allows_revision_by(user):
                raise PermissionDenied
            else:

                post_data = request.POST.copy()

                rev_form = RevisionValidationForm(post_data,
                                        is_iframe_target=is_iframe_target,
                                        section_id=section_id)
                rev_form.parent_slug = slug_dict['parent']
                rev_form.instance.document = doc  # for rev_form.clean()

                # Come up with the original revision to which these changes
                # would be applied.
                orig_rev_id = request.POST.get('current_rev', False)
                if False == orig_rev_id:
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

                else:

                    if 'slug' in post_data:
                        post_data['slug'] = _join_slug(slug_dict['parent_split'], post_data['slug'])

                    # We know now that the form is valid (i.e. slug doesn't have a "/")
                    # Now we can make it a true revision form
                    rev_form = RevisionForm(post_data,
                                            is_iframe_target=is_iframe_target,
                                            section_id=section_id)
                    rev_form.instance.document = doc  # for rev_form.clean()

                    if rev_form.is_valid():
                        _save_rev_and_notify(rev_form, user, doc)

                        if is_iframe_target:
                            # TODO: Does this really need to be a template? Just
                            # shoehorning data into a single HTML element.
                            response = HttpResponse("""
                                <span id="iframe-response"
                                      data-status="OK"
                                      data-current-revision="%s">OK</span>
                            """ % doc.current_revision.id)
                            response['x-frame-options'] = 'SAMEORIGIN'
                            return response

                        if (is_raw and orig_rev is not None and
                                curr_rev.id != orig_rev.id):
                            # If this is the raw view, and there was an original
                            # revision, but the original revision differed from the
                            # current revision at start of editing, we should tell
                            # the client to refresh the page.
                            response = HttpResponse('RESET')
                            response.status_code = 205
                            response['x-frame-options'] = 'SAMEORIGIN'
                            return response

                        if rev_form.instance.is_approved:
                            view = 'wiki.document'
                        else:
                            view = 'wiki.document_revisions'

                        # Construct the redirect URL, adding any needed parameters
                        url = reverse(view, args=[doc.full_path],
                                      locale=doc.locale)
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


    attachments = _format_attachment_obj(doc.attachments)
    allow_add_attachment = Attachment.objects.allow_add_attachment_by(request.user)
    return jingo.render(request, 'wiki/edit_document.html',
                        {'revision_form': rev_form,
                         'document_form': doc_form,
                         'section_id': section_id,
                         'show_translation_parent_block':
                            show_translation_parent_block,
                         'disclose_description': disclose_description,
                         'parent_slug': parent_slug,
                         'parent_path': parent_path,
                         'revision': rev,
                         'document': doc,
                         'allow_add_attachment': allow_add_attachment,
                         'attachment_form': AttachmentRevisionForm(),
                         'attachment_data': attachments,
                         'attachment_data_json': json.dumps(attachments)})


def _edit_document_collision(request, orig_rev, curr_rev, is_iframe_target,
                             is_raw, rev_form, doc_form, section_id, rev, doc):
    """Handle when a mid-air collision is detected upon submission"""

    # Process the content as if it were about to be saved, so that the
    # html_diff is close as possible.
    content = (wiki.content
                .parse(request.POST['content'])
                .injectSectionIDs()
                .serialize())

    # Process the original content for a diff, extracting a section if we're
    # editing one.
    if (doc.is_template):
        curr_content = curr_rev.content
    else:
        tool = wiki.content.parse(curr_rev.content)
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
        response['x-frame-options'] = 'SAMEORIGIN'
        return response

    # Make this response iframe-friendly so we can hack around the
    # save-and-edit iframe button
    response = jingo.render(request, 'wiki/edit_document.html',
                            {'collision': True,
                             'revision_form': rev_form,
                             'document_form': doc_form,
                             'content': content,
                             'current_content': curr_content,
                             'section_id': section_id,
                             'original_revision': orig_rev,
                             'current_revision': curr_rev,
                             'revision': rev,
                             'document': doc})

    response['x-frame-options'] = 'SAMEORIGIN'
    return response


def ckeditor_config(request):
    """Return ckeditor config from database"""
    default_config = EditorToolbar.objects.filter(name='default').all()
    if len(default_config) > 0:
        code = default_config[0].code
    else:
        code = ''
    context = {'editor_config': code}
    return jingo.render(request, 'wiki/ckeditor_config.js', context,
                       mimetype="application/x-javascript")


@login_required
@require_POST
def preview_revision(request):
    """Create an HTML fragment preview of the posted wiki syntax."""
    wiki_content = request.POST.get('content', '')
    kumascript_errors = []
    doc = None
    if request.POST.get('doc_id', False):
        doc = Document.objects.get(id=request.POST.get('doc_id'))

    if kumascript.should_use_rendered(doc, request.GET, html=wiki_content):
        wiki_content, kumascript_errors = kumascript.post(request,
                                                          wiki_content,
                                                          request.locale)
    # TODO: Get doc ID from JSON.
    data = {'content': wiki_content, 'title': request.POST.get('title', ''),
            'kumascript_errors': kumascript_errors}
    #data.update(SHOWFOR_DATA)
    return jingo.render(request, 'wiki/preview.html', data)


@require_GET
def autosuggest_documents(request):
    """Returns the closest title matches for front-end autosuggests"""
    partial_title = request.GET.get('term', '')
    locale = request.GET.get('locale', False)
    current_locale = request.GET.get('current_locale', False)
    exclude_current_locale = request.GET.get('exclude_current_locale', False)

    # TODO: isolate to just approved docs?
    docs = (Document.objects.
        extra(select={'length':'Length(slug)'}).
        filter(title__icontains=partial_title, is_template=0).
        exclude(title__iregex=r'Redirect [0-9]+$').  # New redirect pattern
        exclude(html__iregex=r'^(<p>)?(#)?REDIRECT').  #Legacy redirect
        exclude(slug__icontains='Talk:').  # Remove old talk pages
        order_by('title', 'length'))

    if locale:
        docs = docs.filter(locale=locale)

    if current_locale:
        docs = docs.filter(locale=request.locale)

    if exclude_current_locale:
        docs = docs.exclude(locale=request.locale)

    docs_list = []
    for d in docs:
        doc_info = {
            'title': d.title + ' [' + d.locale + ']',
            'label': d.title,
            'href':  d.get_absolute_url(),
            'id': d.id 
        }
        docs_list.append(doc_info)

    data = json.dumps(docs_list)
    return HttpResponse(data, mimetype='application/json')


@require_GET
@process_document_path
@prevent_indexing
def document_revisions(request, document_slug, document_locale):
    """List all the revisions of a given document."""
    doc = get_object_or_404(
        Document, locale=document_locale, slug=document_slug)
    # Grab revisions, but defer summary and content because they can lead to
    # attempts to cache more than memcached allows.
    revs = (Revision.objects.filter(document=doc)
                .defer('summary', 'content')
                .order_by('-created', '-id'))

    # Ensure the current revision appears at the top, no matter where it
    # appears in the order.
    curr_id = doc.current_revision.id
    revs_out = [r for r in revs if r.id == curr_id]
    revs_out.extend([r for r in revs if r.id != curr_id])

    return jingo.render(request, 'wiki/document_revisions.html',
                        {'revisions': revs_out, 'document': doc})


@login_required
@permission_required('wiki.review_revision')
@process_document_path
def review_revision(request, document_slug, document_locale, revision_id):
    """Review a revision of a wiki document."""
    rev = get_object_or_404(Revision, pk=revision_id,
                            document__slug=document_slug)
    doc = rev.document
    form = ReviewForm()

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid() and not rev.reviewed:
            # Don't allow revisions to be reviewed twice
            rev.is_approved = 'approve' in request.POST
            rev.reviewer = request.user
            rev.reviewed = datetime.now()
            if form.cleaned_data['significance']:
                rev.significance = form.cleaned_data['significance']
            rev.save()

            # Send an email (not really a "notification" in the sense that
            # there's a Watch table entry) to revision creator.
            msg = form.cleaned_data['comment']
            send_reviewed_notification.delay(rev, doc, msg)

            # If approved, send approved notification
            ApproveRevisionInLocaleEvent(rev).fire(exclude=rev.creator)

            # Schedule KB rebuild?
            # schedule_rebuild_kb()

            return HttpResponseRedirect(reverse('wiki.document_revisions',
                                                args=[document.full_path]))

    if doc.parent:  # A translation
        parent_revision = get_current_or_latest_revision(doc.parent)
        template = 'wiki/review_translation.html'
    else:
        parent_revision = None
        template = 'wiki/review_revision.html'

    data = {'revision': rev, 'document': doc, 'form': form,
            'parent_revision': parent_revision}
    data.update(SHOWFOR_DATA)
    return jingo.render(request, template, data)


@require_GET
@process_document_path
@prevent_indexing
def compare_revisions(request, document_slug, document_locale):
    """Compare two wiki document revisions.

    The ids are passed as query string parameters (to and from).

    """
    doc = get_object_or_404(
        Document, locale=document_locale, slug=document_slug)
    if 'from' not in request.GET or 'to' not in request.GET:
        raise Http404

    from_id = smart_int(request.GET.get('from'))
    to_id = smart_int(request.GET.get('to'))
    revision_from = get_object_or_404(Revision, document=doc, id=from_id)
    revision_to = get_object_or_404(Revision, document=doc, id=to_id)

    context = {'document': doc, 'revision_from': revision_from,
                         'revision_to': revision_to}
    if request.GET.get('raw', 0):
        response = jingo.render(request, 'wiki/includes/revision_diff_table.html',
                                context)
    else:
        response = jingo.render(request, 'wiki/compare_revisions.html',
                                context)
    response['x-frame-options'] = 'SAMEORIGIN'
    return response


@login_required
@process_document_path
def select_locale(request, document_slug, document_locale):
    """Select a locale to translate the document to."""
    doc = get_object_or_404(
        Document, locale=document_locale, slug=document_slug)
    return jingo.render(request, 'wiki/select_locale.html', {'document': doc})


@require_http_methods(['GET', 'POST'])
@login_required
@process_document_path
@check_readonly
@prevent_indexing
@transaction.autocommit  # For rendering bookkeeping, needs immediate updates
def translate(request, document_slug, document_locale, revision_id=None):
    """Create a new translation of a wiki document.

    * document_slug is for the default locale
    * translation is to the request locale

    """
    # TODO: Refactor this view into two views? (new, edit)
    # That might help reduce the headache-inducing branchiness.
    parent_doc = get_object_or_404(
        Document, locale=settings.WIKI_DEFAULT_LANGUAGE, slug=document_slug)
    user = request.user

    if not revision_id:
        # HACK: Seems weird, but sticking the translate-to locale in a query
        # param is the best way to avoid the MindTouch-legacy locale
        # redirection logic.
        document_locale = request.REQUEST.get('tolocale',
                                              document_locale)

    # Parese the parent slug
    slug_dict = _split_slug(document_slug)

    # Set a "Discard Changes" page
    discard_href = ''

    if settings.WIKI_DEFAULT_LANGUAGE == document_locale:
        # Don't translate to the default language.
        return HttpResponseRedirect(reverse(
            'wiki.edit_document', locale=settings.WIKI_DEFAULT_LANGUAGE,
            args=[parent_doc.full_path]))

    if not parent_doc.is_localizable:
        message = _lazy(u'You cannot translate this document.')
        return jingo.render(request, 'handlers/400.html',
                            {'message': message}, status=400)

    if revision_id:
        initial_rev = get_object_or_404(Revision, pk=revision_id)

    based_on_rev = get_current_or_latest_revision(parent_doc,
                                                  reviewed_only=False)

    disclose_description = bool(request.GET.get('opendescription'))

    try:
        doc = parent_doc.translations.get(locale=document_locale)
    except Document.DoesNotExist:
        doc = None
        disclose_description = True

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
                   'show_toc': based_on_rev.show_toc}
        if revision_id:
            initial.update(
                content=Revision.objects.get(pk=revision_id).content)
        elif not doc:
            initial.update(content=based_on_rev.content)
        instance = doc and get_current_or_latest_revision(doc)
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
                                                args=[doc.full_path],
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

            rev_form = RevisionValidationForm(post_data)
            rev_form.parent_slug = slug_dict['parent']
            rev_form.instance.document = doc  # for rev_form.clean()

            if rev_form.is_valid() and not doc_form_invalid:
                # append final slug
                post_data['slug'] = destination_slug

                # update the post data with the show_toc of original
                post_data['show_toc'] = based_on_rev.show_toc

                rev_form = RevisionForm(post_data)

                if rev_form.is_valid():
                    _save_rev_and_notify(rev_form, request.user, doc)
                    url = reverse('wiki.document', args=[doc.full_path],
                                  locale=doc.locale)
                    return HttpResponseRedirect(url)

    return jingo.render(request, 'wiki/translate.html',
                        {'parent': parent_doc, 'document': doc,
                         'document_form': doc_form, 'revision_form': rev_form,
                         'locale': document_locale, 'based_on': based_on_rev,
                         'disclose_description': disclose_description,
                         'discard_href': discard_href,
                         'specific_slug': slug_dict['specific'], 'parent_slug': slug_dict['parent']})


@require_POST
@login_required
@process_document_path
def watch_document(request, document_slug, document_locale):
    """Start watching a document for edits."""
    document = get_object_or_404(
        Document, locale=document_locale, slug=document_slug)
    EditDocumentEvent.notify(request.user, document)
    return HttpResponseRedirect(document.get_absolute_url())


@require_POST
@login_required
@process_document_path
def unwatch_document(request, document_slug, document_locale):
    """Stop watching a document for edits."""
    document = get_object_or_404(
        Document, locale=document_locale, slug=document_slug)
    EditDocumentEvent.stop_notifying(request.user, document)
    return HttpResponseRedirect(document.get_absolute_url())


@require_POST
@login_required
def watch_locale(request):
    """Start watching a locale for revisions ready for review."""
    ReviewableRevisionInLocaleEvent.notify(request.user, locale=request.locale)
    # This redirect is pretty bad, because you might also have been on the
    # Contributor Dashboard:
    return HttpResponseRedirect(reverse('dashboards.localization'))


@require_POST
@login_required
def unwatch_locale(request):
    """Stop watching a locale for revisions ready for review."""
    ReviewableRevisionInLocaleEvent.stop_notifying(request.user,
                                                   locale=request.locale)
    return HttpResponseRedirect(reverse('dashboards.localization'))


@require_POST
@login_required
def watch_approved(request):
    """Start watching approved revisions in a locale."""
    locale = request.POST.get('locale')
    if locale not in settings.SUMO_LANGUAGES:
        raise Http404

    ApproveRevisionInLocaleEvent.notify(request.user, locale=locale)
    return HttpResponseRedirect(reverse('dashboards.localization'))


@require_POST
@login_required
def unwatch_approved(request):
    """Stop watching approved revisions."""
    locale = request.POST.get('locale')
    if locale not in settings.SUMO_LANGUAGES:
        raise Http404

    ApproveRevisionInLocaleEvent.stop_notifying(request.user, locale=locale)
    return HttpResponseRedirect(reverse('dashboards.localization'))


@require_GET
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
    data = json.dumps({
        'id': document.id,
        'locale': document.locale,
        'slug': document.slug,
        'title': document.title,
        'summary': document.current_revision.summary,
        'url': document.get_absolute_url(),
    })
    return HttpResponse(data, mimetype='application/json')


@require_GET
@process_document_path
@prevent_indexing
def code_sample(request, document_slug, document_locale, sample_id):
    """Extract a code sample from a document and render it as a standalone
    HTML document"""

    # Restrict rendering of live code samples to specified hosts
    host = request.META.get('HTTP_HOST', '')
    allowed_hosts = constance.config.KUMA_CODE_SAMPLE_HOSTS.split(' ')
    if host not in allowed_hosts:
        raise PermissionDenied

    document = get_object_or_404(Document, slug=document_slug,
                                 locale=document_locale)
    data = document.extract_code_sample(sample_id)
    data['document'] = document
    response = jingo.render(request, 'wiki/code_sample.html', data)
    response['x-frame-options'] = 'ALLOW'
    return response


@require_POST
@process_document_path
def helpful_vote(request, document_slug, document_locale):
    """Vote for Helpful/Not Helpful document"""
    document_locale, document_slug, needs_redirect = (Document
            .locale_and_slug_from_path(document_path, request))

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


@login_required
@check_readonly
def revert_document(request, document_path, revision_id):
    """Revert document to a specific revision."""
    document_locale, document_slug, needs_redirect = (Document
            .locale_and_slug_from_path(document_path, request))

    revision = get_object_or_404(Revision, pk=revision_id,
                                 document__slug=document_slug)
    document = revision.document
    
    if request.method == 'GET':
        # Render the confirmation page
        return jingo.render(request, 'wiki/confirm_revision_revert.html',
                            {'revision': revision, 'document': document})

    document.revert(revision, request.user)
    return HttpResponseRedirect(reverse('wiki.document_revisions',
                                args=[document.full_path]))
    

@login_required
@permission_required('wiki.delete_revision')
@check_readonly
def delete_revision(request, document_path, revision_id):
    """Delete a revision."""
    document_locale, document_slug, needs_redirect = (Document
            .locale_and_slug_from_path(document_path, request))

    revision = get_object_or_404(Revision, pk=revision_id,
                                 document__slug=document_slug)
    document = revision.document

    if request.method == 'GET':
        # Render the confirmation page
        return jingo.render(request, 'wiki/confirm_revision_delete.html',
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
                                        args=[document.full_path]))


def _document_form_initial(document):
    """Return a dict with the document data pertinent for the form."""
    return {'title': document.title,
            'slug': document.slug,
            'category': document.category,
            'is_localizable': document.is_localizable,
            'tags': [t.name for t in document.tags.all()],
            'firefox_versions': [x.item_id for x in
                                 document.firefox_versions.all()],
            'operating_systems': [x.item_id for x in
                                  document.operating_systems.all()]}


def _save_rev_and_notify(rev_form, creator, document):
    """Save the given RevisionForm and send notifications."""
    new_rev = rev_form.save(creator, document)

    document.schedule_rendering('max-age=0')

    # Enqueue notifications
    ReviewableRevisionInLocaleEvent(new_rev).fire(exclude=new_rev.creator)
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


@superuser_required
def load_documents(request):
    """Load documents from uploaded file."""
    form = ImportFileForm()
    if request.method == 'POST':

        # Accept the uploaded document data.
        file_data = None
        form = ImportFileForm(request.POST, request.FILES)
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
    return render_to_response('admin/wiki/document/load_data_form.html',
                              context,
                              context_instance=RequestContext(request))


def raw_file(request, attachment_id, filename):
    """Serve up an attachment's file."""
    # TODO: For now this just grabs and serves the file in the most
    # naive way. This likely has performance and security implications.
    attachment = get_object_or_404(Attachment, pk=attachment_id)
    if attachment.current_revision is None:
        raise Http404
    rev = attachment.current_revision
    resp = HttpResponse(rev.file.read(), mimetype=rev.mime_type)
    resp["Last-Modified"] = rev.created
    resp["Content-Length"] = rev.file.size
    return resp


def mindtouch_file_redirect(request, file_id, filename):
    """Redirect an old MindTouch file URL to a new kuma file URL."""
    attachment = get_object_or_404(Attachment, mindtouch_attachment_id=file_id)
    return HttpResponsePermanentRedirect(attachment.get_file_url())


def attachment_detail(request, attachment_id):
    """Detail view of an attachment."""
    attachment = get_object_or_404(Attachment, pk=attachment_id)
    return jingo.render(request, 'wiki/attachment_detail.html',
                        {'attachment': attachment,
                         'revision': attachment.current_revision})


def attachment_history(request, attachment_id):
    """Detail view of an attachment."""
    # For now this is just attachment_detail with a different
    # template. At some point in the near future, it'd be nice to add
    # a few extra bits, like the ability to set an arbitrary revision
    # to be current.
    attachment = get_object_or_404(Attachment, pk=attachment_id)
    return jingo.render(request, 'wiki/attachment_history.html',
                        {'attachment': attachment,
                         'revision': attachment.current_revision})

@require_POST
@login_required
def new_attachment(request):
    """Create a new Attachment object and populate its initial
    revision."""

    # No access if no permissions to upload
    if not Attachment.objects.allow_add_attachment_by(request.user):
        raise PermissionDenied
    
    form = AttachmentRevisionForm(data=request.POST, files=request.FILES)
    if form.is_valid():
        rev = form.save(commit=False)
        rev.creator = request.user
        attachment = Attachment.objects.create(title=rev.title,
                                               slug=rev.slug)
        rev.attachment = attachment
        rev.save()

        if request.POST.get('is_ajax', ''):
            response = jingo.render(request, 'wiki/includes/attachment_upload_results.html',
                    { 'result': json.dumps(_format_attachment_obj([attachment])) })
        else:
            return HttpResponseRedirect(attachment.get_absolute_url())
    else:
        if request.POST.get('is_ajax', ''):
            error_obj = {
                'title': request.POST.get('is_ajax', ''),
                'error': _(u'The file provided is not valid')
            }
            response = jingo.render(request, 'wiki/includes/attachment_upload_results.html',
                    { 'result': json.dumps([error_obj]) })
        else:
            response = jingo.render(request, 'wiki/edit_attachment.html',
                                    {'form': form})

    response['x-frame-options'] = 'SAMEORIGIN'
    return response


@login_required
def edit_attachment(request, attachment_id):

    # No access if no permissions to upload
    if not request.user.has_perm('wiki.change_attachment'):
        raise PermissionDenied

    attachment = get_object_or_404(Attachment,
                                   pk=attachment_id)
    if request.method == 'POST':
        form = AttachmentRevisionForm(data=request.POST, files=request.FILES)
        if form.is_valid():
            rev = form.save(commit=False)
            rev.creator = request.user
            rev.attachment = attachment
            rev.save()
            return HttpResponseRedirect(attachment.get_absolute_url())
    else:
        form = AttachmentRevisionForm()
    return jingo.render(request, 'wiki/edit_attachment.html',
                        {'form': form})
