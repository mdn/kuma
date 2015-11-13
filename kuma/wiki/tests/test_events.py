import mock
from nose.tools import eq_

from kuma.core.tests import get_user
from kuma.users.tests import UserTestCase

from . import WikiTestCase, revision
from ..events import EditDocumentEvent, context_dict


class NotificationEmailTests(UserTestCase, WikiTestCase):

    def test_context_dict_no_previous_revision(self):
        rev = revision(save=True)
        try:
            cd = context_dict(rev)
        except AttributeError:
            self.fail("Should not throw AttributeError")
        eq_(cd, cd)

    @mock.patch('tidings.events.EventUnion.fire')
    def test_edit_document_event_fires_union(self, mock_union_fire):
        rev = revision(save=True)
        testuser2 = get_user(username='testuser2')
        EditDocumentEvent.notify(testuser2, rev.document)

        EditDocumentEvent(rev).fire()

        assert mock_union_fire.called
