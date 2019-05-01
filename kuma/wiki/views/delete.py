# -*- coding: utf-8 -*-
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import ugettext
from django.views.decorators.cache import never_cache

from kuma.core.decorators import (block_user_agents, login_required,
                                  permission_required)

from ..decorators import check_readonly, process_document_path
from ..forms import DocumentDeletionForm
from ..models import Document, DocumentDeletionLog, Revision
from ..utils import locale_and_slug_from_path


@never_cache
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

    if request.method == 'GET':
        # Render the confirmation page
        return render(request, 'wiki/confirm_revision_revert.html',
                      {'revision': revision, 'document': revision.document})
    else:
        comment = request.POST.get('comment')
        document = revision.document
        old_revision_pk = revision.pk
        try:
            new_revision = document.revert(revision, request.user, comment)
            # schedule a rendering of the new revision if it really was saved
            if new_revision.pk != old_revision_pk:
                document.schedule_rendering('max-age=0')
        except IntegrityError:
            return render(
                request,
                'wiki/confirm_revision_revert.html',
                {
                    'revision': revision,
                    'document': revision.document,
                    'error': ugettext(
                        "Document already exists. Note: You cannot "
                        "revert a document that has been moved until you "
                        "delete its redirect.")
                }
            )
        return redirect('wiki.document_revisions', revision.document.slug)


@never_cache
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
    # TODO: https://bugzil.la/972541 - Deleting a page that has subpages
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
