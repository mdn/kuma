# -*- coding: utf-8 -*-
import newrelic.agent
from tower import ugettext_lazy as _lazy

from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.clickjacking import xframe_options_sameorigin

from ratelimit.decorators import ratelimit
from kuma.core.decorators import login_required, block_user_agents
from kuma.core.utils import smart_int

from .. import kumascript
from ..decorators import process_document_path, prevent_indexing
from ..helpers import format_comment
from ..models import Document, Revision


@block_user_agents
@prevent_indexing
@process_document_path
@newrelic.agent.function_trace()
def revision(request, document_slug, document_locale, revision_id):
    """
    View a wiki document revision.
    """
    rev = get_object_or_404(Revision.objects.select_related('document'),
                            pk=revision_id,
                            document__slug=document_slug)
    context = {
        'document': rev.document,
        'revision': rev,
        'comment': format_comment(rev),
    }
    return render(request, 'wiki/revision.html', context)


@login_required
@require_POST
def preview(request):
    """
    Create an HTML fragment preview of the posted wiki syntax.
    """
    kumascript_errors = []
    doc = None
    render_preview = True

    wiki_content = request.POST.get('content', '')
    doc_id = request.POST.get('doc_id')
    if doc_id:
        doc = Document.objects.get(id=doc_id)

    if doc and doc.defer_rendering:
        render_preview = False
    else:
        render_preview = kumascript.should_use_rendered(doc,
                                                        request.GET,
                                                        html=wiki_content)
    if render_preview:
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


@block_user_agents
@require_GET
@xframe_options_sameorigin
@process_document_path
@prevent_indexing
@ratelimit(key='user_or_ip', rate='15/m', block=True)
def compare(request, document_slug, document_locale):
    """
    Compare two wiki document revisions.

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

    revisions = Revision.objects.prefetch_related('document')
    revision_from = get_object_or_404(revisions, id=from_id, document=doc)
    revision_to = get_object_or_404(revisions, id=to_id, document=doc)

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
@require_POST
@process_document_path
def quick_review(request, document_slug, document_locale):
    """
    Quickly mark a revision as no longer needing a particular type
    of review.
    """
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
        data = {'summary': ' '.join(messages), 'comment': ' '.join(messages)}
        new_rev = doc.revise(request.user, data=data)
        if new_tags:
            new_rev.review_tags.set(*new_tags)
        else:
            new_rev.review_tags.clear()
    return redirect(doc)
