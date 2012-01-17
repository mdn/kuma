from datetime import datetime
import json
import logging
from urllib import urlencode
from string import ascii_letters

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.http import (HttpResponse, HttpResponseRedirect,
                         Http404, HttpResponseBadRequest)
from django.shortcuts import get_object_or_404
from django.views.decorators.http import (require_GET, require_POST,
                                          require_http_methods)

from waffle.decorators import waffle_flag

import jingo
from taggit.models import Tag
from tower import ugettext_lazy as _lazy
from tower import ugettext as _

from access.decorators import permission_required, login_required
from sumo.helpers import urlparams
from sumo.urlresolvers import reverse
from sumo.utils import paginate, smart_int
from wiki import DOCUMENTS_PER_PAGE
from wiki.events import (EditDocumentEvent, ReviewableRevisionInLocaleEvent,
                         ApproveRevisionInLocaleEvent)
from wiki.forms import DocumentForm, RevisionForm, ReviewForm
from wiki.models import (Document, Revision, HelpfulVote, EditorToolbar,
                         ReviewTag,
                         CATEGORIES,
                         OPERATING_SYSTEMS, GROUPED_OPERATING_SYSTEMS,
                         FIREFOX_VERSIONS, GROUPED_FIREFOX_VERSIONS,
                         REVIEW_FLAG_TAGS, get_current_or_latest_revision)
from wiki.parser import wiki_to_html
from wiki.tasks import send_reviewed_notification, schedule_rebuild_kb
import wiki.content


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


@waffle_flag('kumawiki')
@require_GET
def document(request, document_slug):
    """View a wiki document."""
    fallback_reason = None
    # If a slug isn't available in the requested locale, fall back to en-US:
    try:
        doc = Document.objects.get(locale=request.locale, slug=document_slug)
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
        # Look in default language:
        doc = get_object_or_404(Document,
                                locale=settings.WIKI_DEFAULT_LANGUAGE,
                                slug=document_slug)
        # If there's a translation to the requested locale, take it:
        translation = doc.translated_to(request.locale)
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

    # Obey explicit redirect pages:
    # Don't redirect on redirect=no (like Wikipedia), so we can link from a
    # redirected-to-page back to a "Redirected from..." link, so you can edit
    # the redirect.
    redirect_url = (None if request.GET.get('redirect') == 'no'
                    else doc.redirect_url())
    if redirect_url:
        url = urlparams(redirect_url, query_dict=request.GET,
                        redirectslug=doc.slug, redirectlocale=doc.locale)
        return HttpResponseRedirect(url)

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
    #     https://github.com/jsocol/kitsune/commit/f1ebb241e4b1d746f97686e65f49e478e28d89f2

    # Grab some parameters that affect output
    section_id = request.GET.get('section', None)
    show_raw = request.GET.get('raw', False)
    need_edit_links = request.GET.get('edit_links', False)

    # Start applying some filters to the document HTML
    tool = wiki.content.parse(doc.html)

    # If a section ID is specified, extract that section.
    if section_id:
        tool.extractSection(section_id)

    # If this user can edit the document, inject some section editing links.
    if (need_edit_links or not show_raw) and doc.allows_editing_by(request.user):
        tool.injectSectionEditingLinks(doc.slug, doc.locale)

    # if ?raw parameter is supplied, then we respond with raw page source
    # without template wrapping or edit links. This is also permissive for
    # iframe inclusion
    if show_raw:
        response = HttpResponse(tool.serialize())
        response['x-kuma-revision'] = doc.current_revision.id
        response['x-frame-options'] = 'Allow'
        return response
    
    data = {'document': doc, 'document_html': tool.serialize(),
            'redirected_from': redirected_from,
            'related': related, 'contributors': contributors,
            'fallback_reason': fallback_reason}
    data.update(SHOWFOR_DATA)
    return jingo.render(request, 'wiki/document.html', data)


@waffle_flag('kumawiki')
def revision(request, document_slug, revision_id):
    """View a wiki document revision."""
    rev = get_object_or_404(Revision, pk=revision_id,
                            document__slug=document_slug)
    data = {'document': rev.document, 'revision': rev}
    data.update(SHOWFOR_DATA)
    return jingo.render(request, 'wiki/revision.html', data)


@waffle_flag('kumawiki')
@require_GET
def list_documents(request, category=None, tag=None):
    """List wiki documents."""
    if category:
        try:
            category_id = int(category)
        except ValueError:
            raise Http404
        try:
            category = unicode(dict(CATEGORIES)[category_id])
        except KeyError:
            raise Http404

    tag_obj = tag and get_object_or_404(Tag, slug=tag) or None
    docs = Document.objects.filter_for_list(locale=request.locale,
                                             category=category,
                                             tag=tag_obj)
    docs = paginate(request, docs, per_page=DOCUMENTS_PER_PAGE)
    return jingo.render(request, 'wiki/list_documents.html',
                        {'documents': docs,
                         'category': category,
                         'tag': tag})


@waffle_flag('kumawiki')
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


@waffle_flag('kumawiki')
@login_required
def new_document(request):
    """Create a new wiki document."""
    if request.method == 'GET':
        doc_form = DocumentForm(
            can_create_tags=request.user.has_perm('taggit.add_tag'))
        rev_form = RevisionForm(initial={'review_tags': [t[0] for t in REVIEW_FLAG_TAGS]})
        return jingo.render(request, 'wiki/new_document.html',
                            {'document_form': doc_form,
                             'revision_form': rev_form})

    post_data = request.POST.copy()
    post_data.update({'locale': request.locale})
    doc_form = DocumentForm(post_data,
        can_create_tags=request.user.has_perm('taggit.add_tag'))
    rev_form = RevisionForm(post_data)

    if doc_form.is_valid() and rev_form.is_valid():
        doc = doc_form.save(None)
        _save_rev_and_notify(rev_form, request.user, doc)
        if doc.current_revision.is_approved:
            view = 'wiki.document'
        else:
            view = 'wiki.document_revisions'
        return HttpResponseRedirect(reverse(view,
                                    args=[doc.slug]))

    return jingo.render(request, 'wiki/new_document.html',
                        {'document_form': doc_form,
                         'revision_form': rev_form})


@waffle_flag('kumawiki')
@require_http_methods(['GET', 'POST'])
@login_required  # TODO: Stop repeating this knowledge here and in
                 # Document.allows_editing_by.
def edit_document(request, document_slug, revision_id=None):
    """Create a new revision of a wiki document, or edit document metadata."""
    doc = get_object_or_404(
        Document, locale=request.locale, slug=document_slug)
    user = request.user

    # If this document has a parent, then the edit is handled by the
    # translate view. Pass it on.
    if doc.parent:
        return translate(request, doc.parent.slug, revision_id)
    if revision_id:
        rev = get_object_or_404(Revision, pk=revision_id, document=doc)
    else:
        rev = doc.current_revision or doc.revisions.order_by('-created',
                                                             '-id')[0]

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
        doc_form = DocumentForm(initial=_document_form_initial(doc),
            can_create_tags=user.has_perm('taggit.add_tag'))

    if request.method == 'GET':
        if not (rev_form or doc_form):
            # You can't do anything on this page, so get lost.
            raise PermissionDenied
    else:  # POST

        is_iframe_target = request.GET.get('iframe', False)
        is_raw = request.GET.get('raw', False)
        need_edit_links = request.GET.get('edit_links', False)

        # Comparing against localized names for the Save button bothers me, so
        # I embedded a hidden input:
        which_form = request.POST.get('form')

        if which_form == 'doc':
            if doc.allows_editing_by(user):
                post_data = request.POST.copy()
                post_data.update({'locale': request.locale})
                doc_form = DocumentForm(post_data, instance=doc,
                    can_create_tags=user.has_perm('taggit.add_tag'))
                if doc_form.is_valid():
                    # Get the possibly new slug for the imminent redirection:
                    doc = doc_form.save(None)

                    # Do we need to rebuild the KB?
                    _maybe_schedule_rebuild(doc_form)

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
                                          args=[doc.slug]),
                                  opendescription=1))
                disclose_description = True
            else:
                raise PermissionDenied

        elif which_form == 'rev':
            if not doc.allows_revision_by(user):
                raise PermissionDenied
            else:
                rev_form = RevisionForm(request.POST, 
                                        is_iframe_target=is_iframe_target,
                                        section_id=section_id)
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
                        return _edit_document_collision(request,
                                                        orig_rev, curr_rev,
                                                        is_iframe_target,
                                                        is_raw,
                                                        rev_form, doc_form,
                                                        section_id, 
                                                        rev, doc)

                else:
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

    return jingo.render(request, 'wiki/edit_document.html',
                        {'revision_form': rev_form,
                         'document_form': doc_form,
                         'section_id': section_id,
                         'disclose_description': disclose_description,
                         'revision': rev,
                         'document': doc})


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


@waffle_flag('kumawiki')
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


@waffle_flag('kumawiki')
@login_required
@require_POST
def preview_revision(request):
    """Create an HTML fragment preview of the posted wiki syntax."""
    wiki_content = request.POST.get('content', '')
    # TODO: Get doc ID from JSON.
    data = {'content': wiki_content}
    #data.update(SHOWFOR_DATA)
    return jingo.render(request, 'wiki/preview.html', data)


@waffle_flag('kumawiki')
@require_GET
def document_revisions(request, document_slug):
    """List all the revisions of a given document."""
    doc = get_object_or_404(
        Document, locale=request.locale, slug=document_slug)
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


@waffle_flag('kumawiki')
@login_required
@permission_required('wiki.review_revision')
def review_revision(request, document_slug, revision_id):
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
            schedule_rebuild_kb()

            return HttpResponseRedirect(reverse('wiki.document_revisions',
                                                args=[document_slug]))

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


@waffle_flag('kumawiki')
@require_GET
def compare_revisions(request, document_slug):
    """Compare two wiki document revisions.

    The ids are passed as query string parameters (to and from).

    """
    doc = get_object_or_404(
        Document, locale=request.locale, slug=document_slug)
    if 'from' not in request.GET or 'to' not in request.GET:
        raise Http404

    from_id = smart_int(request.GET.get('from'))
    to_id = smart_int(request.GET.get('to'))
    revision_from = get_object_or_404(Revision, document=doc, id=from_id)
    revision_to = get_object_or_404(Revision, document=doc, id=to_id)

    return jingo.render(request, 'wiki/compare_revisions.html',
                        {'document': doc, 'revision_from': revision_from,
                         'revision_to': revision_to})


@waffle_flag('kumawiki')
@login_required
def select_locale(request, document_slug):
    """Select a locale to translate the document to."""
    doc = get_object_or_404(
        Document, locale=settings.WIKI_DEFAULT_LANGUAGE, slug=document_slug)
    return jingo.render(request, 'wiki/select_locale.html', {'document': doc})


@waffle_flag('kumawiki')
@require_http_methods(['GET', 'POST'])
@login_required
def translate(request, document_slug, revision_id=None):
    """Create a new translation of a wiki document.

    * document_slug is for the default locale
    * translation is to the request locale

    """
    # TODO: Refactor this view into two views? (new, edit)
    # That might help reduce the headache-inducing branchiness.
    parent_doc = get_object_or_404(
        Document, locale=settings.WIKI_DEFAULT_LANGUAGE, slug=document_slug)
    user = request.user

    if settings.WIKI_DEFAULT_LANGUAGE == request.locale:
        # Don't translate to the default language.
        return HttpResponseRedirect(reverse(
            'wiki.edit_document', locale=settings.WIKI_DEFAULT_LANGUAGE,
            args=[parent_doc.slug]))

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
        doc = parent_doc.translations.get(locale=request.locale)
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
        doc_initial = _document_form_initial(doc) if doc else None
        doc_form = DocumentForm(initial=doc_initial,
            can_create_tags=user.has_perm('taggit.add_tag'))
    if user_has_rev_perm:
        initial = {'based_on': based_on_rev.id, 'comment': ''}
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

        if user_has_doc_perm and which_form in ['doc', 'both']:
            disclose_description = True
            post_data = request.POST.copy()
            post_data.update({'locale': request.locale})
            doc_form = DocumentForm(post_data, instance=doc,
                can_create_tags=user.has_perm('taggit.add_tag'))
            doc_form.instance.locale = request.locale
            doc_form.instance.parent = parent_doc
            if which_form == 'both':
                rev_form = RevisionForm(request.POST)

            # If we are submitting the whole form, we need to check that
            # the Revision is valid before saving the Document.
            if doc_form.is_valid() and (which_form == 'doc' or
                                        rev_form.is_valid()):
                doc = doc_form.save(parent_doc)

                # Possibly schedule a rebuild.
                _maybe_schedule_rebuild(doc_form)

                if which_form == 'doc':
                    url = urlparams(reverse('wiki.edit_document',
                                            args=[doc.slug]),
                                    opendescription=1)
                    return HttpResponseRedirect(url)

                doc_slug = doc_form.cleaned_data['slug']
            else:
                doc_form_invalid = True
        else:
            doc_slug = doc.slug

        if doc and user_has_rev_perm and which_form in ['rev', 'both']:
            rev_form = RevisionForm(request.POST)
            rev_form.instance.document = doc  # for rev_form.clean()
            if rev_form.is_valid() and not doc_form_invalid:
                _save_rev_and_notify(rev_form, request.user, doc)
                url = reverse('wiki.document_revisions',
                              args=[doc_slug])
                return HttpResponseRedirect(url)

    return jingo.render(request, 'wiki/translate.html',
                        {'parent': parent_doc, 'document': doc,
                         'document_form': doc_form, 'revision_form': rev_form,
                         'locale': request.locale, 'based_on': based_on_rev,
                         'disclose_description': disclose_description})


@waffle_flag('kumawiki')
@require_POST
@login_required
def watch_document(request, document_slug):
    """Start watching a document for edits."""
    document = get_object_or_404(
        Document, locale=request.locale, slug=document_slug)
    EditDocumentEvent.notify(request.user, document)
    return HttpResponseRedirect(document.get_absolute_url())


@waffle_flag('kumawiki')
@require_POST
@login_required
def unwatch_document(request, document_slug):
    """Stop watching a document for edits."""
    document = get_object_or_404(
        Document, locale=request.locale, slug=document_slug)
    EditDocumentEvent.stop_notifying(request.user, document)
    return HttpResponseRedirect(document.get_absolute_url())


@waffle_flag('kumawiki')
@require_POST
@login_required
def watch_locale(request):
    """Start watching a locale for revisions ready for review."""
    ReviewableRevisionInLocaleEvent.notify(request.user, locale=request.locale)
    # This redirect is pretty bad, because you might also have been on the
    # Contributor Dashboard:
    return HttpResponseRedirect(reverse('dashboards.localization'))


@waffle_flag('kumawiki')
@require_POST
@login_required
def unwatch_locale(request):
    """Stop watching a locale for revisions ready for review."""
    ReviewableRevisionInLocaleEvent.stop_notifying(request.user,
                                                   locale=request.locale)
    return HttpResponseRedirect(reverse('dashboards.localization'))


@waffle_flag('kumawiki')
@require_POST
@login_required
def watch_approved(request):
    """Start watching approved revisions in a locale."""
    locale = request.POST.get('locale')
    if locale not in settings.SUMO_LANGUAGES:
        raise Http404

    ApproveRevisionInLocaleEvent.notify(request.user, locale=locale)
    return HttpResponseRedirect(reverse('dashboards.localization'))


@waffle_flag('kumawiki')
@require_POST
@login_required
def unwatch_approved(request):
    """Stop watching approved revisions."""
    locale = request.POST.get('locale')
    if locale not in settings.SUMO_LANGUAGES:
        raise Http404

    ApproveRevisionInLocaleEvent.stop_notifying(request.user, locale=locale)
    return HttpResponseRedirect(reverse('dashboards.localization'))


@waffle_flag('kumawiki')
@require_GET
def json_view(request, document_slug=None):
    """Return some basic document info in a JSON blob."""
    kwargs = {'locale': request.locale, 'current_revision__isnull': False}
    if document_slug is not None:
        kwargs['slug'] = document_slug
        kwargs['locale'] = request.locale
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


@waffle_flag('kumawiki')
@require_POST
def helpful_vote(request, document_slug):
    """Vote for Helpful/Not Helpful document"""
    document = get_object_or_404(
        Document, locale=request.locale, slug=document_slug)

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


@waffle_flag('kumawiki')
@login_required
@permission_required('wiki.delete_revision')
def delete_revision(request, document_slug, revision_id):
    """Delete a revision."""
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
            is_approved=True).order_by('-reviewed')
        if revs.count() > 1:
            document.current_revision = revs[1]
        else:
            document.current_revision = None
        document.html = document.content_cleaned or ''
        document.save()

    revision.delete()

    return HttpResponseRedirect(reverse('wiki.document_revisions',
                                        args=[document.slug]))


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

    # Enqueue notifications
    ReviewableRevisionInLocaleEvent(new_rev).fire(exclude=new_rev.creator)
    EditDocumentEvent(new_rev).fire(exclude=new_rev.creator)


def _maybe_schedule_rebuild(form):
    """Try to schedule a KB rebuild if a title or slug has changed."""
    if 'title' in form.changed_data or 'slug' in form.changed_data:
        schedule_rebuild_kb()
