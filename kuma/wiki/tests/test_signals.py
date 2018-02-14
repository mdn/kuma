import pytest

from kuma.wiki.models import Revision, Document


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
