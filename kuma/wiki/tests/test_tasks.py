from datetime import datetime

from kuma.users.models import User
from kuma.users.tests import UserTestCase

from ..models import DocumentDeletionLog, DocumentSpamAttempt
from ..tasks import (
    delete_logs_for_purged_documents,
    delete_old_documentspamattempt_data,
)


class DeleteOldDocumentSpamAttemptData(UserTestCase):
    fixtures = UserTestCase.fixtures

    def test_delete_old_data(self):
        user = User.objects.get(username="testuser01")
        admin = User.objects.get(username="admin")
        new_dsa = DocumentSpamAttempt.objects.create(
            user=user,
            title="new record",
            slug="users:me",
            data='{"PII": "IP, email, etc."}',
        )
        old_reviewed_dsa = DocumentSpamAttempt.objects.create(
            user=user,
            title="old ham",
            data='{"PII": "plenty"}',
            review=DocumentSpamAttempt.HAM,
            reviewer=admin,
        )
        old_unreviewed_dsa = DocumentSpamAttempt.objects.create(
            user=user, title="old unknown", data='{"PII": "yep"}'
        )

        # created is auto-set to current time, update bypasses model logic
        old_date = datetime(2015, 1, 1)
        ids = [old_reviewed_dsa.id, old_unreviewed_dsa.id]
        DocumentSpamAttempt.objects.filter(id__in=ids).update(created=old_date)

        delete_old_documentspamattempt_data()

        new_dsa.refresh_from_db()
        assert new_dsa.data is not None

        old_reviewed_dsa.refresh_from_db()
        assert old_reviewed_dsa.data is None
        assert old_reviewed_dsa.review == DocumentSpamAttempt.HAM

        old_unreviewed_dsa.refresh_from_db()
        assert old_unreviewed_dsa.data is None
        assert old_unreviewed_dsa.review == (DocumentSpamAttempt.REVIEW_UNAVAILABLE)


def test_delete_logs_for_purged_documents(root_doc, wiki_user):
    ddl1 = DocumentDeletionLog.objects.create(
        locale=root_doc.locale, slug=root_doc.slug, user=wiki_user, reason="Doomed."
    )
    root_doc.delete()  # Soft-delete it
    DocumentDeletionLog.objects.create(
        locale="en-US", slug="HardDeleted", user=wiki_user, reason="Purged."
    )
    delete_logs_for_purged_documents()
    assert list(DocumentDeletionLog.objects.all()) == [ddl1]
