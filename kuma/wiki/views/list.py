# -*- coding: utf-8 -*-
from django.http import Http404
from django.shortcuts import get_object_or_404, get_list_or_404, render
from django.views.decorators.http import require_GET

from kuma.core.decorators import block_user_agents
from kuma.core.utils import paginate

from ..constants import DOCUMENTS_PER_PAGE
from ..decorators import process_document_path, prevent_indexing
from ..models import (Document, DocumentTag, Revision, ReviewTag,
                      LocalizationTag)
from ..queries import MultiQuerySet


@block_user_agents
@require_GET
def documents(request, category=None, tag=None):
    """
    List wiki documents depending on the optionally given category or tag.
    """
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
    return render(request, 'wiki/list/documents.html', context)


@block_user_agents
@require_GET
def templates(request):
    """
    Returns listing of all templates
    """
    docs = Document.objects.filter(is_template=True).order_by('title')
    paginated_docs = paginate(request, docs, per_page=DOCUMENTS_PER_PAGE)
    context = {
        'documents': paginated_docs,
        'count': docs.count(),
        'is_templates': True,
    }
    return render(request, 'wiki/list/documents.html', context)


@block_user_agents
@require_GET
def tags(request):
    """
    Returns listing of all tags
    """
    tags = DocumentTag.objects.order_by('name')
    tags = paginate(request, tags, per_page=DOCUMENTS_PER_PAGE)
    return render(request, 'wiki/list/tags.html', {'tags': tags})


@block_user_agents
@require_GET
def needs_review(request, tag=None):
    """
    Lists wiki documents with revisions flagged for review
    """
    tag_obj = tag and get_object_or_404(ReviewTag, name=tag) or None
    docs = Document.objects.filter_for_review(locale=request.locale,
                                              tag=tag_obj)
    paginated_docs = paginate(request, docs, per_page=DOCUMENTS_PER_PAGE)
    context = {
        'documents': paginated_docs,
        'count': docs.count(),
        'tag': tag_obj,
        'tag_name': tag,
    }
    return render(request, 'wiki/list/needs_review.html', context)


@block_user_agents
@require_GET
def with_localization_tag(request, tag=None):
    """
    Lists wiki documents with localization tag
    """
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
    return render(request, 'wiki/list/with_localization_tags.html', context)


@block_user_agents
@require_GET
def with_errors(request):
    """
    Lists wiki documents with (KumaScript) errors
    """
    docs = Document.objects.filter_for_list(locale=request.locale, errors=True)
    paginated_docs = paginate(request, docs, per_page=DOCUMENTS_PER_PAGE)
    context = {
        'documents': paginated_docs,
        'count': docs.count(),
        'errors': True,
    }
    return render(request, 'wiki/list/documents.html', context)


@block_user_agents
@require_GET
def without_parent(request):
    """Lists wiki documents without parent (no English source document)"""
    docs = Document.objects.filter_for_list(locale=request.locale,
                                            noparent=True)
    paginated_docs = paginate(request, docs, per_page=DOCUMENTS_PER_PAGE)
    context = {
        'documents': paginated_docs,
        'count': docs.count(),
        'noparent': True,
    }
    return render(request, 'wiki/list/documents.html', context)


@block_user_agents
@require_GET
def top_level(request):
    """Lists documents directly under /docs/"""
    docs = Document.objects.filter_for_list(locale=request.locale,
                                            toplevel=True)
    paginated_docs = paginate(request, docs, per_page=DOCUMENTS_PER_PAGE)
    context = {
        'documents': paginated_docs,
        'count': docs.count(),
        'toplevel': True,
    }
    return render(request, 'wiki/list/documents.html', context)


@block_user_agents
@require_GET
@process_document_path
@prevent_indexing
def revisions(request, document_slug, document_locale):
    """
    List all the revisions of a given document.
    """
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
    return render(request, 'wiki/list/revisions.html', context)
