from datetime import datetime
import json
from string import ascii_letters

from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect, Http404
from django.conf import settings

import jingo
from tower import ugettext_lazy as _lazy

from sumo.urlresolvers import reverse
from .models import (Document, Revision, CATEGORIES, OPERATING_SYSTEMS,
                     FIREFOX_VERSIONS, GROUPED_FIREFOX_VERSIONS)
from .forms import DocumentForm, RevisionForm, ReviewForm
from .tasks import send_reviewed_notification


OS_ABBR_JSON = json.dumps(dict([(o.slug, True)
                                for o in OPERATING_SYSTEMS]))
BROWSER_ABBR_JSON = json.dumps(dict([(v.slug, True)
                                     for v in FIREFOX_VERSIONS]))
MISSING_MSG = _lazy('[missing header]')


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


def document(request, document_slug):
    """View a wiki document."""
    # This may change depending on how we decide to structure
    # the url and handle locales.
    doc = get_object_or_404(
        Document, locale=request.locale, slug=document_slug)
    return jingo.render(request, 'wiki/document.html',
                        {'document': doc,
                         'oses': OPERATING_SYSTEMS,
                         'oses_json': OS_ABBR_JSON,
                         'browsers': GROUPED_FIREFOX_VERSIONS,
                         'browsers_json': BROWSER_ABBR_JSON,
                         'version_group_json': VERSION_GROUP_JSON,
                         'missing_msg_json': json.dumps(unicode(MISSING_MSG))})


def list_documents(request, category=None):
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
    return jingo.render(request, 'wiki/list_documents.html',
                        {'documents': docs,
                         'category': category})


@login_required
@permission_required('wiki.add_document')
def new_document(request):
    """Create a new wiki document."""
    if request.method == 'GET':
        doc_form = DocumentForm()
        rev_form = RevisionForm()
        return jingo.render(request, 'wiki/new_document.html',
                            {'document_form': doc_form,
                             'revision_form': rev_form})

    doc_form = DocumentForm(request.POST)
    rev_form = RevisionForm(request.POST)

    if doc_form.is_valid() and rev_form.is_valid():
        doc = doc_form.save(commit=False)
        doc.locale = request.locale
        doc.save()
        doc_form.save_m2m()

        doc.firefox_versions = doc_form.cleaned_data['firefox_versions']
        doc.operating_systems = doc_form.cleaned_data['operating_systems']

        rev = rev_form.save(commit=False)
        rev.document = doc
        rev.creator = request.user
        rev.save()

        return HttpResponseRedirect(reverse('wiki.document_revisions',
                                    args=[doc.slug]))

    return jingo.render(request, 'wiki/new_document.html',
                        {'document_form': doc_form,
                         'revision_form': rev_form})


@login_required  # TODO: Stop repeating this knowledge here and in
                 # Document.allows_editing_by.
def new_revision(request, document_slug, revision_id=None):
    """Create a new revision of a wiki document in default locale."""
    doc = get_object_or_404(
        Document, locale=request.locale, slug=document_slug)

    if not doc.allows_editing_by(request.user):
        raise PermissionDenied

    # If this document has a parent then the edit is handled by the
    # translate view, redirect there.
    if doc.parent:
        return HttpResponseRedirect(reverse('wiki.translate',
                                            args=[doc.parent.slug]))

    if revision_id:
        rev = get_object_or_404(Revision, pk=revision_id, document=doc)
    elif doc.current_revision:
        rev = doc.current_revision
    else:
        rev = doc.revisions.order_by('-created')[0]

    if request.method == 'GET':
        rev_form = RevisionForm(initial=_revision_form_initial(rev))

        # If the Document doesn't have a current_revision (nothing approved)
        # then all the Document fields are still editable. Once there is an
        # approved Revision, the Document fields are locked.
        if not doc.current_revision:
            doc_form = DocumentForm(initial=_document_form_initial(doc))
        else:
            doc_form = None

    else:  # POST
        rev_form = RevisionForm(request.POST)
        if not doc.current_revision:
            doc_form = DocumentForm(request.POST)
        else:
            doc_form = None

        if rev_form.is_valid() and (not doc_form or doc_form.is_valid()):
            _process_doc_and_rev_form(doc_form, rev_form, request.locale,
                                      request.user, None, rev, doc)

            return HttpResponseRedirect(reverse('wiki.document_revisions',
                                                args=[document_slug]))

    return jingo.render(request, 'wiki/new_revision.html',
                        {'revision_form': rev_form,
                         'document_form': doc_form,
                         'document': doc})


def document_revisions(request, document_slug):
    """List all the revisions of a given document."""
    doc = get_object_or_404(
        Document, locale=request.locale, slug=document_slug)
    revs = Revision.objects.filter(document=doc).order_by('-created')

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

            return HttpResponseRedirect(reverse('wiki.document_revisions',
                                                args=[document_slug]))

    if doc.parent:  # A translation
        template = 'wiki/review_translation.html'
    else:
        template = 'wiki/review_revision.html'
    return jingo.render(request, template,
                        {'revision': rev, 'document': doc, 'form': form})


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
@permission_required('wiki.add_revision')
def translate(request, document_slug):
    """Create a new translation of a wiki document.

    * document_slug is for the default locale
    * translation is to the request locale

    """
    if settings.WIKI_DEFAULT_LANGUAGE == request.locale:
        # Don't translate to the default
        raise Http404

    parent_doc = get_object_or_404(
        Document, locale=settings.WIKI_DEFAULT_LANGUAGE, slug=document_slug)
    try:
        doc = parent_doc.translations.get(locale=request.locale)
    except Document.DoesNotExist:
        doc = None

    if request.method == 'GET':
        if doc:
            doc_initial = _document_form_initial(doc)
            if doc.current_revision:
                rev = doc.current_revision
            else:
                rev = doc.revisions.order_by('-created')[0]
            rev_initial = _revision_form_initial(rev)
        else:
            doc_initial = None
            rev_initial = None

        doc_form = DocumentForm(initial=doc_initial)
        rev_form = RevisionForm(initial=rev_initial)
    else:  # POST
        doc_form = DocumentForm(request.POST)
        rev_form = RevisionForm(request.POST)
        if doc_form.is_valid() and rev_form.is_valid():
            _process_doc_and_rev_form(
                doc_form, rev_form, request.locale, request.user,
                parent_doc, parent_doc.current_revision, doc)

            url = reverse('wiki.document_revisions',
                          args=[doc_form.cleaned_data['slug']])
            return HttpResponseRedirect(url)

    return jingo.render(request, 'wiki/translate.html',
                        {'parent': parent_doc, 'document': doc,
                         'document_form': doc_form, 'revision_form': rev_form,
                         'locale': request.locale})


def _document_form_initial(document):
    """Return a dict with the document data pertinent for the form."""
    return {'title': document.title,
            'slug': document.slug,
            'category': document.category,
            'tags': ','.join([t.name for t in document.tags.all()]),
            'firefox_versions': [x.item_id for x in
                                 document.firefox_versions.all()],
            'operating_systems': [x.item_id for x in
                                  document.operating_systems.all()]}


def _revision_form_initial(revision):
    """Return a dict with the revision data pertinent for the form."""
    return {'keywords': revision.keywords, 'content': revision.content,
            'summary': revision.summary}


def _process_doc_and_rev_form(document_form, revision_form, locale, user,
                              parent_doc, base_revision, document=None):
    """Persist the Document and Revision forms."""
    if document_form:
        doc = document_form.save(commit=False)
        doc.locale = locale
        doc.parent = parent_doc
        if document:
            doc.id = document.id
        doc.save()

        # TODO: Use the tagging widget instead of this?
        tags = document_form.cleaned_data['tags']
        doc.tags.exclude(name__in=tags).delete()
        doc.tags.add(*tags)

        ffv = document_form.cleaned_data['firefox_versions']
        doc.firefox_versions.exclude(
            item_id__in=[x.item_id for x in ffv]).delete()
        doc.firefox_versions = ffv
        os = document_form.cleaned_data['operating_systems']
        doc.operating_systems.exclude(
            item_id__in=[x.item_id for x in os]).delete()
        doc.operating_systems = os
    else:
        doc = document

    new_rev = revision_form.save(commit=False)
    new_rev.document = doc
    new_rev.creator = user
    new_rev.based_on = base_revision
    new_rev.save()
