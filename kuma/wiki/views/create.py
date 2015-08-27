# -*- coding: utf-8 -*-
import newrelic.agent

from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import render

from constance import config

from kuma.attachments.forms import AttachmentRevisionForm
from kuma.attachments.models import Attachment
from kuma.core.decorators import never_cache, login_required, block_user_agents
from kuma.core.urlresolvers import reverse

from ..constants import (TEMPLATE_TITLE_PREFIX,
                         REVIEW_FLAG_TAGS_DEFAULT)
from ..decorators import check_readonly, prevent_indexing
from ..forms import DocumentForm, RevisionForm, RevisionValidationForm
from ..models import Document, Revision
from .utils import save_revision_and_notify


@block_user_agents
@login_required
@check_readonly
@prevent_indexing
@never_cache
@newrelic.agent.function_trace()
def new_document(request):
    """Create a new wiki document."""

    initial_slug = request.GET.get('slug', '')
    initial_title = initial_slug.replace('_', ' ')

    initial_parent_id = ''
    try:
        initial_parent_id = int(request.GET.get('parent', ''))
    except ValueError:
        pass

    clone_id = None
    try:
        clone_id = int(request.GET.get('clone', ''))
    except ValueError:
        pass

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
            pass

    if request.method == 'GET':

        initial_data = {}
        initial_html = ''
        initial_tags = ''
        initial_toc = Revision.TOC_DEPTH_H4

        if clone_id:
            try:
                clone_doc = Document.objects.get(pk=clone_id)
                initial_title = clone_doc.title
                initial_html = clone_doc.html
                initial_tags = clone_doc.tags.all()
                if clone_doc.current_revision:
                    initial_toc = clone_doc.current_revision.toc_depth
                else:
                    initial_toc = 1

            except Document.DoesNotExist:
                pass

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
            'content': initial_html,
            'review_tags': review_tags,
            'tags': initial_tags,
            'toc_depth': initial_toc
        })

        allow_add_attachment = (
            Attachment.objects.allow_add_attachment_by(request.user))
        context = {
            'is_template': is_template,
            'parent_slug': parent_slug,
            'parent_id': initial_parent_id,
            'document_form': doc_form,
            'revision_form': rev_form,
            'WIKI_DOCUMENT_TAG_SUGGESTIONS': config.WIKI_DOCUMENT_TAG_SUGGESTIONS,
            'initial_tags': initial_tags,
            'allow_add_attachment': allow_add_attachment,
            'attachment_form': AttachmentRevisionForm(),
            'parent_path': parent_path}

        return render(request, 'wiki/new_document.html', context)

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
            save_revision_and_notify(rev_form, request, doc)
            if doc.current_revision.is_approved:
                view = 'wiki.document'
            else:
                view = 'wiki.document_revisions'
            return HttpResponseRedirect(reverse(view, args=[doc.slug]))
        else:
            doc_form.data['slug'] = posted_slug
    else:
        doc_form.data['slug'] = posted_slug

    allow_add_attachment = (
        Attachment.objects.allow_add_attachment_by(request.user))

    context = {
        'is_template': is_template,
        'document_form': doc_form,
        'revision_form': rev_form,
        'WIKI_DOCUMENT_TAG_SUGGESTIONS': config.WIKI_DOCUMENT_TAG_SUGGESTIONS,
        'allow_add_attachment': allow_add_attachment,
        'attachment_form': AttachmentRevisionForm(),
        'parent_slug': parent_slug,
        'parent_path': parent_path,
    }
    return render(request, 'wiki/new_document.html', context)
