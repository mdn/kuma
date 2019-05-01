import mock
import pytest

from kuma.wiki.models import Document
from kuma.wiki.signals import render_done


@mock.patch('kuma.api.signal_handlers.publish')
def test_render_signal(publish_mock, root_doc):
    """The document is published on the render_done signal."""
    render_done.send(sender=Document, instance=root_doc)
    publish_mock.delay.assert_called_once_with([root_doc.pk])


@pytest.mark.parametrize('case', ('normal', 'redirect'))
@mock.patch('kuma.api.signal_handlers.unpublish')
def test_post_delete_signal(unpublish_mock, root_doc, redirect_doc, case):
    """The document is unpublished after it is deleted."""
    doc = root_doc if case == 'normal' else redirect_doc
    doc.delete()
    unpublish_mock.delay.assert_called_once_with([(doc.locale, doc.slug)])
