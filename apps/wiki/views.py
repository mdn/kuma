from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from django.http import HttpResponseRedirect, Http404

import jingo

from sumo.urlresolvers import reverse
from .models import Document, Revision, CATEGORIES
from .forms import DocumentForm, RevisionForm


#log = logging.getLogger('k.wiki')


def document(request, document_slug):
    """View a wiki document."""
    # This may change depending on how we decide to structure
    # the url and handle locales.
    doc = get_object_or_404(Document, title=document_slug.replace('+', ' '))
    return jingo.render(request, 'wiki/document.html',
                        {'document': doc})


def list_documents(request, category=None):
    """List wiki documents."""
    docs = Document.objects.all()
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
        form = DocumentForm()
        return jingo.render(request, 'wiki/new_document.html', {'form': form})

    form = DocumentForm(request.POST)

    if form.is_valid():
        doc = form.save()

        # TODO: firefox_versions + operating_systems

        return HttpResponseRedirect(reverse('wiki.document_revisions',
                                    args=[doc.id]))

    return jingo.render(request, 'wiki/new_document.html', {'form': form})


@login_required
@permission_required('wiki.add_revision')
def new_revision(request, document_id, based_on=None):
    """Create a new revision of a wiki document."""
    doc = get_object_or_404(Document, pk=document_id)
    if request.method == 'GET':
        form = RevisionForm()
        return jingo.render(request, 'wiki/new_revision.html',
                            {'form': form, 'document': doc})

    form = RevisionForm(request.POST)

    if form.is_valid():
        rev = form.save(commit=False)
        rev.document = doc
        rev.creator = request.user
        rev.save()

        return HttpResponseRedirect(reverse('wiki.document_revisions',
                                            args=[document_id]))

    return jingo.render(request, 'wiki/new_revision.html',
                        {'form': form, 'document': doc})


def document_revisions(request, document_id):
    """List all the revisions of a given document."""
    doc = get_object_or_404(Document, pk=document_id)
    revs = Revision.objects.filter(document=doc)
    return jingo.render(request, 'wiki/document_revisions.html',
                        {'revisions': revs,
                         'document': doc})
