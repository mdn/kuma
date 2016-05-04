# -*- coding: utf-8 -*-
import newrelic.agent

from constance import config
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect

from kuma.attachments.forms import AttachmentRevisionForm
from kuma.core.decorators import never_cache, login_required, block_user_agents
from kuma.core.urlresolvers import reverse

from ..constants import (DEV_DOC_REQUEST_FORM,
                         TEMPLATE_TITLE_PREFIX,
                         REVIEW_FLAG_TAGS_DEFAULT)
from ..decorators import check_readonly, prevent_indexing
from ..forms import DocumentForm, RevisionForm
from ..models import Document, Revision


@newrelic.agent.function_trace()
@block_user_agents
@login_required
@check_readonly
@prevent_indexing
@never_cache
def create(request):
    """
    Create a new wiki page, which is a document and a revision.
    """
    initial_slug = request.GET.get('slug', '')

    # Try to head off disallowed Template:* creation, right off the bat
    if not Document.objects.allows_add_by(request.user, initial_slug):
        raise PermissionDenied
    # TODO: Integrate this into a new exception-handling middleware
    if not request.user.has_perm('wiki.add_document'):
        context = {
            'reason': 'create-page',
            'request_page_url': DEV_DOC_REQUEST_FORM,
            'email_address': config.EMAIL_LIST_MDN_ADMINS
        }
        return render(request, '403-create-page.html', context=context,
                      status=403)

    # if the initial slug indicates the creation of a new template
    is_template = initial_slug.startswith(TEMPLATE_TITLE_PREFIX)

    # a fake title based on the initial slug passed via a query parameter
    initial_title = initial_slug.replace('_', ' ')

    # in case we want to create a sub page under a different document
    try:
        # If a parent ID is provided via GET, confirm it exists
        initial_parent_id = int(request.GET.get('parent', ''))
        parent_doc = Document.objects.get(pk=initial_parent_id)
        parent_slug = parent_doc.slug
        parent_path = parent_doc.get_absolute_url()
    except (ValueError, Document.DoesNotExist):
        initial_parent_id = parent_slug = parent_path = ''

    # in case we want to create a new page by cloning an existing document
    try:
        clone_id = int(request.GET.get('clone', ''))
    except ValueError:
        clone_id = None

    context = {
        'is_template': is_template,
        'attachment_form': AttachmentRevisionForm(),
        'parent_path': parent_path,
        'parent_slug': parent_slug,
    }

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

        doc_form = DocumentForm(initial=initial_data, parent_slug=parent_slug)

        initial = {
            'slug': initial_slug,
            'title': initial_title,
            'content': initial_html,
            'review_tags': review_tags,
            'tags': initial_tags,
            'toc_depth': initial_toc
        }
        rev_form = RevisionForm(request=request, initial=initial)

        context.update({
            'parent_id': initial_parent_id,
            'document_form': doc_form,
            'revision_form': rev_form,
            'initial_tags': initial_tags,
        })

    else:

        submitted_data = request.POST.copy()
        posted_slug = submitted_data['slug']
        submitted_data['locale'] = request.LANGUAGE_CODE
        if parent_slug:
            submitted_data['parent_topic'] = initial_parent_id

        doc_form = DocumentForm(data=submitted_data, parent_slug=parent_slug)
        rev_form = RevisionForm(request=request,
                                data=submitted_data,
                                parent_slug=parent_slug)

        if doc_form.is_valid() and rev_form.is_valid():
            slug = doc_form.cleaned_data['slug']
            if not Document.objects.allows_add_by(request.user, slug):
                raise PermissionDenied

            doc = doc_form.save(parent=None)
            rev_form.save(doc)
            if doc.current_revision.is_approved:
                view = 'wiki.document'
            else:
                view = 'wiki.document_revisions'
            return redirect(reverse(view, args=[doc.slug]))
        else:
            doc_form.data['slug'] = posted_slug

        context.update({
            'document_form': doc_form,
            'revision_form': rev_form,
        })

    return render(request, 'wiki/create.html', context)
