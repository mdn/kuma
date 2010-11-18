from datetime import datetime
import json
import logging
from string import ascii_letters

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import (HttpResponse, HttpResponseRedirect,
                         Http404, HttpResponseBadRequest)
from django.shortcuts import get_object_or_404
from django.views.decorators.http import (require_GET, require_POST,
                                          require_http_methods)

import jingo
from taggit.models import Tag
from tower import ugettext_lazy as _lazy
from tower import ugettext as _

from access.decorators import permission_required
from notifications import create_watch, destroy_watch
from sumo.helpers import urlparams
from sumo.urlresolvers import reverse
from sumo.utils import paginate
from wiki import DOCUMENTS_PER_PAGE
from wiki.forms import DocumentForm, RevisionForm, ReviewForm
from wiki.models import (Document, Revision, HelpfulVote, CATEGORIES,
                         OPERATING_SYSTEMS, GROUPED_OPERATING_SYSTEMS,
                         FIREFOX_VERSIONS, GROUPED_FIREFOX_VERSIONS)
from wiki.parser import wiki_to_html
from wiki.tasks import (send_reviewed_notification,
                        send_ready_for_review_notification,
                        send_edited_notification,
                        schedule_rebuild_kb)


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


@require_GET
def document(request, document_slug):
    """View a wiki document."""
    # If a slug isn't available in the requested locale, fall back to en-US:
    try:
        doc = Document.objects.get(locale=request.locale, slug=document_slug)
    except Document.DoesNotExist:
        # Look in default language:
        doc = get_object_or_404(Document,
                                locale=settings.WIKI_DEFAULT_LANGUAGE,
                                slug=document_slug)
        # If there's a translation to the requested locale, take it:
        translation = doc.translated_to(request.locale)
        if translation:
            doc = translation
        return HttpResponseRedirect(doc.get_absolute_url())

    # Obey explicit redirect pages:
    # Don't redirect on redirect=no (like Wikipedia), so we can link from a
    # redirected-to-page back to a "Redirected from..." link, so you can edit
    # the redirect.
    redirect_url = (None if request.GET.get('redirect') == 'no'
                    else doc.redirect_url())
    if redirect_url:
        return HttpResponseRedirect(urlparams(redirect_url,
                                              redirectslug=doc.slug,
                                              redirectlocale=doc.locale))

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
    contributors = doc.revisions.filter(
        is_approved=True).values_list('creator__username', flat=True)

    data = {'document': doc, 'redirected_from': redirected_from,
            'related': related, 'contributors': contributors.distinct()}
    data.update(SHOWFOR_DATA)
    return jingo.render(request, 'wiki/document.html', data)


def revision(request, document_slug, revision_id):
    """View a wiki document revision."""
    rev = get_object_or_404(Revision, pk=revision_id,
                            document__slug=document_slug)
    data = {'document': rev.document, 'revision': rev}
    data.update(SHOWFOR_DATA)
    return jingo.render(request, 'wiki/revision.html', data)


@require_GET
def list_documents(request, category=None, tag=None):
    """List wiki documents."""
    docs = Document.objects.filter(locale=request.locale)
    if category:
        docs = docs.filter(category=category)
        try:
            category_id = int(category)
        except ValueError:
            raise Http404
        try:
            category = unicode(dict(CATEGORIES)[category_id])
        except KeyError:
            raise Http404

    if tag:
        tagobj = get_object_or_404(Tag, slug=tag)
        docs = docs.filter(tags__in=[tagobj.name])

    docs = paginate(request, docs, per_page=DOCUMENTS_PER_PAGE)
    return jingo.render(request, 'wiki/list_documents.html',
                        {'documents': docs,
                         'category': category,
                         'tag': tag})


@login_required
def new_document(request):
    """Create a new wiki document."""
    if request.method == 'GET':
        doc_form = DocumentForm(
            can_create_tags=request.user.has_perm('taggit.add_tag'))
        rev_form = RevisionForm()
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
        return HttpResponseRedirect(reverse('wiki.document_revisions',
                                    args=[doc.slug]))

    return jingo.render(request, 'wiki/new_document.html',
                        {'document_form': doc_form,
                         'revision_form': rev_form})


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
        return translate(request, doc.parent.slug)

    if revision_id:
        rev = get_object_or_404(Revision, pk=revision_id, document=doc)
    else:
        rev = doc.current_revision or doc.revisions.order_by('-created',
                                                             '-id')[0]

    disclose_description = bool(request.GET.get('opendescription'))
    doc_form = rev_form = None
    if doc.allows_revision_by(user):
        rev_form = RevisionForm(instance=rev, initial={'based_on': rev.id,
                                                       'comment': ''})
    if doc.allows_editing_by(user):
        doc_form = DocumentForm(initial=_document_form_initial(doc),
            can_create_tags=user.has_perm('taggit.add_tag'))

    if request.method == 'GET':
        if not (rev_form or doc_form):
            # You can't do anything on this page, so get lost.
            raise PermissionDenied
    else:  # POST
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

                    return HttpResponseRedirect(
                        urlparams(reverse('wiki.edit_document',
                                          args=[doc.slug]),
                                  opendescription=1))
                disclose_description = True
            else:
                raise PermissionDenied
        elif which_form == 'rev':
            if doc.allows_revision_by(user):
                rev_form = RevisionForm(request.POST)
                rev_form.instance.document = doc  # for rev_form.clean()
                if rev_form.is_valid():
                    _save_rev_and_notify(rev_form, user, doc)
                    return HttpResponseRedirect(
                        reverse('wiki.document_revisions',
                                args=[document_slug]))
            else:
                raise PermissionDenied

    return jingo.render(request, 'wiki/edit_document.html',
                        {'revision_form': rev_form,
                         'document_form': doc_form,
                         'disclose_description': disclose_description,
                         'document': doc})


@login_required
@require_POST
def preview_revision(request):
    """Create an HTML fragment preview of the posted wiki syntax."""
    wiki_content = request.POST.get('content', '')
    data = {'content': wiki_to_html(wiki_content, request.locale)}
    data.update(SHOWFOR_DATA)
    return jingo.render(request, 'wiki/preview.html', data)


@require_GET
def document_revisions(request, document_slug):
    """List all the revisions of a given document."""
    doc = get_object_or_404(
        Document, locale=request.locale, slug=document_slug)
    revs = Revision.objects.filter(document=doc).order_by('-created', '-id')

    return jingo.render(request, 'wiki/document_revisions.html',
                        {'revisions': revs, 'document': doc})


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

            # Send notification to revision creator.
            msg = form.cleaned_data['comment']
            send_reviewed_notification.delay(rev, doc, msg)

            # Schedule KB rebuild?
            schedule_rebuild_kb()

            return HttpResponseRedirect(reverse('wiki.document_revisions',
                                                args=[document_slug]))

    if doc.parent:  # A translation
        template = 'wiki/review_translation.html'
    else:
        template = 'wiki/review_revision.html'
    return jingo.render(request, template,
                        {'revision': rev, 'document': doc, 'form': form})


@require_GET
def compare_revisions(request, document_slug):
    """Compare two wiki document revisions.

    The ids are passed as query string parameters (to and from).

    """
    doc = get_object_or_404(
        Document, locale=request.locale, slug=document_slug)
    if 'from' not in request.GET or 'to' not in request.GET:
        raise Http404

    revision_from = get_object_or_404(Revision, document=doc,
                                      id=request.GET.get('from'))
    revision_to = get_object_or_404(Revision, document=doc,
                                    id=request.GET.get('to'))

    return jingo.render(request, 'wiki/compare_revisions.html',
                        {'document': doc, 'revision_from': revision_from,
                         'revision_to': revision_to})


@login_required
def select_locale(request, document_slug):
    """Select a locale to translate the document to."""
    doc = get_object_or_404(
        Document, locale=settings.WIKI_DEFAULT_LANGUAGE, slug=document_slug)
    return jingo.render(request, 'wiki/select_locale.html', {'document': doc})


@require_http_methods(['GET', 'POST'])
@login_required
def translate(request, document_slug):
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
        message = _lazy('You cannot translate this document.')
        return jingo.render(request, 'handlers/400.html',
                            {'message': message}, status=400)

    based_on_rev = _get_current_or_latest_revision(parent_doc)
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
        if not doc:
            initial.update(content=based_on_rev.content)
        rev_form = RevisionForm(instance=doc and doc.current_revision,
                                initial=initial)

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
                         'locale': request.locale,
                         'disclose_description': disclose_description})


@require_POST
@login_required
def watch_document(request, document_slug):
    """Start watching a document for edits."""
    document = get_object_or_404(
        Document, locale=request.locale, slug=document_slug)
    create_watch(Document, document.id, request.user.email, 'edited')
    return HttpResponseRedirect(document.get_absolute_url())


@require_POST
@login_required
def unwatch_document(request, document_slug):
    """Stop watching a document for edits."""
    document = get_object_or_404(
        Document, locale=request.locale, slug=document_slug)
    destroy_watch(Document, document.id, request.user.email)
    return HttpResponseRedirect(document.get_absolute_url())


@require_POST
@login_required
def watch_locale(request):
    """Start watching a locale for revisions ready for review."""
    create_watch(Document, None, request.user.email, 'ready_for_review',
                 request.locale)
    return HttpResponseRedirect(reverse('dashboards.localization'))


@require_POST
@login_required
def unwatch_locale(request):
    """Stop watching a locale for revisions ready for review."""
    destroy_watch(Document, None, request.user.email, 'ready_for_review',
                  request.locale)
    return HttpResponseRedirect(reverse('dashboards.localization'))


@require_GET
def json_view(request):
    """Return some basic document info in a JSON blob."""
    kwargs = {'locale': request.locale, 'current_revision__isnull': False}
    if 'title' in request.GET:
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
        document.html = document.content_parsed or ''
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
    send_ready_for_review_notification.delay(new_rev, document)
    send_edited_notification.delay(new_rev, document)


def _maybe_schedule_rebuild(form):
    """Try to schedule a KB rebuild if a title or slug has changed."""
    if 'title' in form.changed_data or 'slug' in form.changed_data:
        schedule_rebuild_kb()


def _get_current_or_latest_revision(document):
    """Returns current revision if there is one, else the last created
    revision."""
    rev = document.current_revision
    if not rev:
        revs = document.revisions.exclude(
            is_approved=False, reviewed__isnull=False).order_by('-created')
        if revs.exists():
            rev = revs[0]

    return rev
