from __future__ import unicode_literals

import mock
import pytest

from ..models import Document, Revision
from ..signals import render_done


@pytest.mark.tags
def test_on_document_save_signal_invalidated_tags_cache(root_doc, wiki_user):

    tags1 = ('JavaScript', 'AJAX', 'DOM')
    Revision.objects.create(document=root_doc, tags=','.join(tags1), creator=wiki_user)

    # cache the tags of the document and check its the tag that we created and it is sorted
    assert sorted(tags1) == root_doc.all_tags_name

    # Create another revision with some other tags and check tags get invalidate and get updated
    tags2 = ('foo', 'bar')
    Revision.objects.create(document=root_doc, tags=','.join(tags2), creator=wiki_user)

    doc = Document.objects.get(id=root_doc.id)

    assert sorted(tags2) == doc.all_tags_name


@mock.patch('kuma.wiki.signal_handlers.build_json_data_for_document')
def test_render_signal(build_json_task, root_doc):
    """The JSON is rebuilt when a Document is done rendering."""
    render_done.send(
        sender=Document, instance=root_doc, invalidate_cdn_cache=False)
    assert build_json_task.delay.called


@mock.patch('kuma.wiki.signal_handlers.build_json_data_for_document')
def test_render_signal_doc_deleted(build_json_task, root_doc):
    """The JSON is not rebuilt when a deleted Document is done rendering."""
    root_doc.deleted = True
    render_done.send(
        sender=Document, instance=root_doc, invalidate_cdn_cache=False)
    assert not build_json_task.delay.called
