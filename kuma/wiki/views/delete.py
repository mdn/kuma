# -*- coding: utf-8 -*-
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from kuma.core.decorators import login_required, permission_required, block_user_agents
from kuma.core.urlresolvers import reverse

from ..decorators import check_readonly, process_document_path
from ..forms import DocumentDeletionForm
from ..models import Document, Revision, DocumentDeletionLog
from ..utils import locale_and_slug_from_path


@block_user_agents
@login_required
@check_readonly
def revert_document(request, document_path, revision_id):
    """
    Revert document to a specific revision.
    """
    document_locale, document_slug, needs_redirect = (
        locale_and_slug_from_path(document_path, request))

    revision = get_object_or_404(Revision.objects.select_related('document'),
                                 pk=revision_id,
                                 document__slug=document_slug)

    if not revision.document.allows_revision_by(request.user):
        raise PermissionDenied

    if request.method == 'GET':
        # Render the confirmation page
        return render(request, 'wiki/confirm_revision_revert.html',
                      {'revision': revision, 'document': revision.document})
    else:
        comment = request.POST.get('comment')
        revision.document.revert(revision, request.user, comment)
        return redirect('wiki.document_revisions', revision.document.slug)


@block_user_agents
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
            return redirect(document)
    else:
        form = DocumentDeletionForm()

    context = {
        'document': document,
        'form': form,
        'request': request,
        'revision': first_revision,
        'prevent': prevent,
    }
    return render(request, 'wiki/confirm_document_delete.html', context)


@block_user_agents
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
    return redirect(document)


@block_user_agents
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
    if request.method == 'POST' and 'confirm' in request.POST:
        document.purge()
        return redirect(reverse('wiki.document',
                                args=(document_slug,),
                                locale=document_locale))
    else:
        return render(request,
                      'wiki/confirm_purge.html',
                      {'document': document})
