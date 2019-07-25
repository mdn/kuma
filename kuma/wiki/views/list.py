# -*- coding: utf-8 -*-
from django.shortcuts import get_list_or_404, get_object_or_404, render
from django.views.decorators.http import require_GET
from ratelimit.decorators import ratelimit

from kuma.core.decorators import (block_user_agents, ensure_wiki_domain,
                                  shared_cache_control)
from kuma.core.utils import paginate

from ..constants import DOCUMENTS_PER_PAGE
from ..decorators import prevent_indexing, process_document_path
from ..models import (Document, DocumentTag, LocalizationTag, ReviewTag,
                      Revision)


@ensure_wiki_domain
@shared_cache_control
@block_user_agents
@require_GET
@ratelimit(key='user_or_ip', rate='40/m', block=True)
def documents(request, tag=None):
    """
    List wiki documents depending on the optionally given tag.
    """
    # Taggit offers a slug - but use name here, because the slugification
    # stinks and is hard to customize.
    tag_obj = None
    if tag:
        matching_tags = get_list_or_404(DocumentTag, name__iexact=tag)
        for matching_tag in matching_tags:
            if matching_tag.name.lower() == tag.lower():
                tag_obj = matching_tag
                break
    docs = Document.objects.filter_for_list(locale=request.LANGUAGE_CODE,
                                            tag=tag_obj)
    paginated_docs = paginate(request, docs, per_page=DOCUMENTS_PER_PAGE)
    context = {
        'documents': paginated_docs,
        'tag': tag,
    }
    return render(request, 'wiki/list/documents.html', context)


@ensure_wiki_domain
@shared_cache_control
@block_user_agents
@require_GET
@ratelimit(key='user_or_ip', rate='40/m', block=True)
def tags(request):
    """
    Returns listing of all tags
    """
    tags = DocumentTag.objects.order_by('name')
    tags = paginate(request, tags, per_page=DOCUMENTS_PER_PAGE)
    return render(request, 'wiki/list/tags.html', {'tags': tags})


@ensure_wiki_domain
@shared_cache_control
@block_user_agents
@require_GET
@ratelimit(key='user_or_ip', rate='40/m', block=True)
def needs_review(request, tag=None):
    """
    Lists wiki documents with revisions flagged for review
    """
    tag_obj = tag and get_object_or_404(ReviewTag, name=tag) or None
    docs = Document.objects.filter_for_review(locale=request.LANGUAGE_CODE,
                                              tag=tag_obj)
    paginated_docs = paginate(request, docs, per_page=DOCUMENTS_PER_PAGE)
    context = {
        'documents': paginated_docs,
        'count': docs.count(),
        'tag': tag_obj,
        'tag_name': tag,
    }
    return render(request, 'wiki/list/needs_review.html', context)


@ensure_wiki_domain
@shared_cache_control
@block_user_agents
@require_GET
@ratelimit(key='user_or_ip', rate='40/m', block=True)
def with_localization_tag(request, tag=None):
    """
    Lists wiki documents with localization tag
    """
    tag_obj = tag and get_object_or_404(LocalizationTag, name=tag) or None
    docs = Document.objects.filter_with_localization_tag(
        locale=request.LANGUAGE_CODE, tag=tag_obj)
    paginated_docs = paginate(request, docs, per_page=DOCUMENTS_PER_PAGE)
    context = {
        'documents': paginated_docs,
        'count': docs.count(),
        'tag': tag_obj,
        'tag_name': tag,
    }
    return render(request, 'wiki/list/with_localization_tags.html', context)


@ensure_wiki_domain
@shared_cache_control
@block_user_agents
@require_GET
@ratelimit(key='user_or_ip', rate='40/m', block=True)
def with_errors(request):
    """
    Lists wiki documents with (KumaScript) errors
    """
    docs = Document.objects.filter_for_list(locale=request.LANGUAGE_CODE,
                                            errors=True)
    paginated_docs = paginate(request, docs, per_page=DOCUMENTS_PER_PAGE)
    context = {
        'documents': paginated_docs,
        'errors': True,
    }
    return render(request, 'wiki/list/documents.html', context)


@ensure_wiki_domain
@shared_cache_control
@block_user_agents
@require_GET
@ratelimit(key='user_or_ip', rate='40/m', block=True)
def without_parent(request):
    """Lists wiki documents without parent (no English source document)"""
    docs = Document.objects.filter_for_list(locale=request.LANGUAGE_CODE,
                                            noparent=True)
    paginated_docs = paginate(request, docs, per_page=DOCUMENTS_PER_PAGE)
    context = {
        'documents': paginated_docs,
        'noparent': True,
    }
    return render(request, 'wiki/list/documents.html', context)


@ensure_wiki_domain
@shared_cache_control
@block_user_agents
@require_GET
@ratelimit(key='user_or_ip', rate='400/m', block=True)
def top_level(request):
    """Lists documents directly under /docs/"""
    docs = Document.objects.filter_for_list(locale=request.LANGUAGE_CODE,
                                            toplevel=True)
    paginated_docs = paginate(request, docs, per_page=DOCUMENTS_PER_PAGE)
    context = {
        'documents': paginated_docs,
        'toplevel': True,
    }
    return render(request, 'wiki/list/documents.html', context)


@ensure_wiki_domain
@shared_cache_control
@block_user_agents
@require_GET
@process_document_path
@prevent_indexing
@ratelimit(key='user_or_ip', rate='20/m', block=True)
def revisions(request, document_slug, document_locale):
    """
    List all the revisions of a given document.
    """
    locale = request.GET.get('locale', document_locale)

    # Load document with only fields for history display
    doc_query = (Document.objects
                 .only('id', 'locale', 'slug', 'title',
                       'current_revision_id',
                       'parent__slug', 'parent__locale')
                 .select_related('parent')
                 .exclude(current_revision__isnull=True)
                 .filter(locale=locale, slug=document_slug))
    document = get_object_or_404(doc_query)

    # Process the requested page size
    per_page = request.GET.get('limit', 10)
    if not request.user.is_authenticated and per_page == 'all':
        return render(request, '403.html',
                      {'reason': 'revisions_login_required'}, status=403)

    # Get ordered revision IDs
    revision_ids = list(document.revisions
                        .order_by('-created', '-id')
                        .values_list('id', flat=True))

    # Create pairs (this revision, previous revision)
    revision_pairs = list(zip(revision_ids, revision_ids[1:] + [None]))

    # Paginate the revision pairs, or use all of them
    if per_page == 'all':
        page = None
        selected_revision_pairs = revision_pairs
    else:
        try:
            per_page = int(per_page)
        except ValueError:
            per_page = DOCUMENTS_PER_PAGE

        page = paginate(request, revision_pairs, per_page)
        selected_revision_pairs = list(page.object_list)

    # Include original English revision of the first translation
    earliest_id, earliest_prev_id = selected_revision_pairs[-1]
    if earliest_prev_id is None and document.parent:
        earliest = Revision.objects.only('based_on').get(id=earliest_id)
        if earliest.based_on is not None:
            selected_revision_pairs[-1] = (earliest_id, earliest.based_on_id)
            selected_revision_pairs.append((earliest.based_on_id, None))

    # Gather revisions on this history page, restricted to display fields
    selected_revision_ids = [rev_id for rev_id, _ in selected_revision_pairs]
    previous_id = selected_revision_pairs[-1][1]
    if previous_id is not None:
        selected_revision_ids.append(previous_id)
    selected_revisions = (Revision.objects
                          .only('id', 'slug', 'created', 'comment',
                                'document__slug', 'document__locale',
                                'creator__username', 'creator__is_active')
                          .select_related('document', 'creator')
                          .filter(id__in=selected_revision_ids))
    revisions = {rev.id: rev for rev in selected_revisions}

    context = {
        'selected_revision_pairs': selected_revision_pairs,
        'revisions': revisions,
        'document': document,
        'page': page,
    }
    return render(request, 'wiki/list/revisions.html', context)
