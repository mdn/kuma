# -*- coding: utf-8 -*-
import textwrap
from urllib import urlencode

import newrelic.agent
from tower import ugettext as _

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.http import require_http_methods

from jingo.helpers import urlparams
from ratelimit.decorators import ratelimit

from kuma.attachments.forms import AttachmentRevisionForm
from kuma.core.decorators import never_cache, login_required, block_user_agents
from kuma.core.urlresolvers import reverse
from kuma.core.utils import limit_banned_ip_to_0

import kuma.wiki.content
from ..decorators import (check_readonly, process_document_path,
                          prevent_indexing)
from ..forms import DocumentForm, RevisionForm
from ..models import Document, Revision

from .translate import translate
from .utils import document_form_initial, split_slug


@xframe_options_sameorigin
def _edit_document_collision(request, orig_rev, curr_rev, is_iframe_target,
                             is_raw, rev_form, doc_form, section_id, rev, doc):
    """
    Handle when a mid-air collision is detected upon submission
    """
    # Process the content as if it were about to be saved, so that the
    # html_diff is close as possible.
    content = (kuma.wiki.content.parse(request.POST['content'])
                                .injectSectionIDs()
                                .serialize())

    # Process the original content for a diff, extracting a section if we're
    # editing one.
    if doc.is_template:
        curr_content = curr_rev.content
    else:
        parsed_content = kuma.wiki.content.parse(curr_rev.content)
        parsed_content.injectSectionIDs()
        if section_id:
            parsed_content.extractSection(section_id)
        curr_content = parsed_content.serialize()

    if is_raw:
        # When dealing with the raw content API, we need to signal the conflict
        # differently so the client-side can escape out to a conflict
        # resolution UI.
        response = HttpResponse('CONFLICT')
        response.status_code = 409
        return response

    # Make this response iframe-friendly so we can hack around the
    # save-and-edit iframe button
    context = {
        'collision': True,
        'revision_form': rev_form,
        'document_form': doc_form,
        'content': content,
        'current_content': curr_content,
        'section_id': section_id,
        'original_revision': orig_rev,
        'current_revision': curr_rev,
        'revision': rev,
        'document': doc,
    }
    return render(request, 'wiki/edit.html', context)


@block_user_agents
@require_http_methods(['GET', 'POST'])
@login_required  # TODO: Stop repeating this knowledge here and in Document.allows_editing_by.
@ratelimit(key='user', rate=limit_banned_ip_to_0, block=True)
@process_document_path
@check_readonly
@prevent_indexing
@never_cache
@newrelic.agent.function_trace()
def edit(request, document_slug, document_locale, revision_id=None):
    """
    Create a new revision of a wiki document, or edit document metadata.
    """
    doc = get_object_or_404(Document,
                            locale=document_locale,
                            slug=document_slug)

    # If this document has a parent, then the edit is handled by the
    # translate view. Pass it on.
    if doc.parent and doc.parent.id != doc.id:
        return translate(request, doc.parent.slug, doc.locale, revision_id,
                         bypass_process_document_path=True)
    if revision_id:
        rev = get_object_or_404(Revision, pk=revision_id, document=doc)
    else:
        rev = doc.current_revision or doc.revisions.order_by('-created',
                                                             '-id')[0]

    # Keep hold of the full post slug
    slug_dict = split_slug(document_slug)
    # Update the slug, removing the parent path, and
    # *only* using the last piece.
    # This is only for the edit form.
    rev.slug = slug_dict['specific']

    section_id = request.GET.get('section', None)
    if section_id and not request.is_ajax():
        return HttpResponse(_("Sections may only be edited inline."))
    disclose_description = bool(request.GET.get('opendescription'))

    doc_form = rev_form = None
    if doc.allows_revision_by(request.user):
        rev_form = RevisionForm(request=request,
                                instance=rev,
                                initial={'based_on': rev.id,
                                         'current_rev': rev.id,
                                         'comment': ''},
                                section_id=section_id)
    if doc.allows_editing_by(request.user):
        doc_form = DocumentForm(initial=document_form_initial(doc))

    # Need to make check *here* to see if this could have a translation parent
    show_translation_parent_block = (
        (document_locale != settings.WIKI_DEFAULT_LANGUAGE) and
        (not doc.parent_id))

    if request.method == 'GET':
        if not (rev_form or doc_form):
            # You can't do anything on this page, so get lost.
            raise PermissionDenied

    else:  # POST
        is_iframe_target = request.GET.get('iframe', False)
        is_raw = request.GET.get('raw', False)
        need_edit_links = request.GET.get('edit_links', False)
        parent_id = request.POST.get('parent_id', '')

        # Attempt to set a parent
        if show_translation_parent_block and parent_id:
            try:
                parent_doc = get_object_or_404(Document, id=parent_id)
                doc.parent = parent_doc
            except Document.DoesNotExist:
                pass

        # Comparing against localized names for the Save button bothers me, so
        # I embedded a hidden input:
        which_form = request.POST.get('form')

        if which_form == 'doc':
            if doc.allows_editing_by(request.user):
                post_data = request.POST.copy()

                post_data.update({'locale': document_locale})
                doc_form = DocumentForm(post_data, instance=doc)
                if doc_form.is_valid():
                    # if must be here for section edits
                    if 'slug' in post_data:
                        post_data['slug'] = u'/'.join([slug_dict['parent'],
                                                       post_data['slug']])

                    # Get the possibly new slug for the imminent redirection:
                    doc = doc_form.save(parent=None)

                    if is_iframe_target:
                        # TODO: Does this really need to be a template? Just
                        # shoehorning data into a single HTML element.
                        response = HttpResponse(textwrap.dedent("""
                            <span id="iframe-response"
                                  data-status="OK"
                                  data-current-revision="%s">OK</span>
                        """ % doc.current_revision.id))
                        response['X-Frame-Options'] = 'SAMEORIGIN'
                        return response

                    return redirect(urlparams(doc.get_edit_url(),
                                              opendescription=1))
                disclose_description = True
            else:
                raise PermissionDenied

        elif which_form == 'rev':
            if not doc.allows_revision_by(request.user):
                raise PermissionDenied
            else:
                post_data = request.POST.copy()

                rev_form = RevisionForm(request=request,
                                        data=post_data,
                                        is_iframe_target=is_iframe_target,
                                        section_id=section_id)
                rev_form.instance.document = doc  # for rev_form.clean()

                # Come up with the original revision to which these changes
                # would be applied.
                orig_rev_id = request.POST.get('current_rev', False)
                if orig_rev_id is False:
                    orig_rev = None
                else:
                    orig_rev = Revision.objects.get(pk=orig_rev_id)
                # Get the document's actual current revision.
                curr_rev = doc.current_revision

                if not rev_form.is_valid():
                    # Was there a mid-air collision?
                    if 'current_rev' in rev_form._errors:
                        # Jump out to a function to escape indentation hell
                        return _edit_document_collision(
                            request, orig_rev, curr_rev, is_iframe_target,
                            is_raw, rev_form, doc_form, section_id,
                            rev, doc)

                if rev_form.is_valid():
                    rev_form.save(doc)

                    if is_iframe_target:
                        # TODO: Does this really need to be a template? Just
                        # shoehorning data into a single HTML element.
                        response = HttpResponse("""
                            <span id="iframe-response"
                                  data-status="OK"
                                  data-current-revision="%s">OK</span>
                        """ % doc.current_revision.id)
                        response['X-Frame-Options'] = 'SAMEORIGIN'
                        return response

                    if (is_raw and orig_rev is not None and
                            curr_rev.id != orig_rev.id):
                        # If this is the raw view, and there was an original
                        # revision, but the original revision differed from the
                        # current revision at start of editing, we should tell
                        # the client to refresh the page.
                        response = HttpResponse('RESET')
                        response['X-Frame-Options'] = 'SAMEORIGIN'
                        response.status_code = 205
                        return response

                    if rev_form.instance.is_approved:
                        view = 'wiki.document'
                    else:
                        view = 'wiki.document_revisions'

                    # Construct the redirect URL, adding any needed parameters
                    url = reverse(view, args=[doc.slug], locale=doc.locale)
                    params = {}
                    if is_raw:
                        params['raw'] = 'true'
                        if need_edit_links:
                            # Only need to carry over ?edit_links with ?raw,
                            # because they're on by default in the normal UI
                            params['edit_links'] = 'true'
                        if section_id:
                            # If a section was edited, and we're using the raw
                            # content API, constrain to that section.
                            params['section'] = section_id
                    if params:
                        url = '%s?%s' % (url, urlencode(params))
                    if not is_raw and section_id:
                        # If a section was edited, jump to the section anchor
                        # if we're not getting raw content.
                        url = '%s#%s' % (url, section_id)

                    return redirect(url)

    parent_path = parent_slug = ''
    if slug_dict['parent']:
        parent_slug = slug_dict['parent']

    if doc.parent_topic_id:
        parent_doc = Document.objects.get(pk=doc.parent_topic_id)
        parent_path = parent_doc.get_absolute_url()
        parent_slug = parent_doc.slug

    context = {
        'revision_form': rev_form,
        'document_form': doc_form,
        'section_id': section_id,
        'disclose_description': disclose_description,
        'parent_slug': parent_slug,
        'parent_path': parent_path,
        'revision': rev,
        'document': doc,
        'attachment_form': AttachmentRevisionForm(),
    }
    return render(request, 'wiki/edit.html', context)
