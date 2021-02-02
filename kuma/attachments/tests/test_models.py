import datetime

from django.core.files.base import ContentFile
from django.db.utils import IntegrityError

from kuma.users.tests import UserTestCase
from kuma.wiki.models import DocumentAttachment
from kuma.wiki.tests import document

from ..models import Attachment, AttachmentRevision, TrashedAttachment


class AttachmentModelTests(UserTestCase):
    def setUp(self):
        super(AttachmentModelTests, self).setUp()
        self.test_user = self.user_model.objects.get(username="testuser2")
        self.attachment = Attachment(title="some title")
        self.attachment.save()
        self.revision = AttachmentRevision(
            attachment=self.attachment,
            mime_type="text/plain",
            title=self.attachment.title,
            description="some description",
            created=datetime.datetime.now(),
            is_approved=True,
        )
        self.revision.creator = self.test_user
        self.revision.file.save(
            "filename.txt", ContentFile(b"Meh meh I am a test file.")
        )

        self.revision2 = AttachmentRevision(
            attachment=self.attachment,
            mime_type="text/plain",
            title=self.attachment.title,
            description="some description",
            created=datetime.datetime.now(),
            is_approved=True,
        )
        self.revision2.creator = self.test_user
        self.revision2.file.save(
            "filename2.txt", ContentFile(b"Meh meh I am a test file.")
        )
        self.storage = AttachmentRevision.file.field.storage

    def test_document_attachment(self):
        doc = document(save=True)
        self.assertEqual(DocumentAttachment.objects.count(), 0)

        document_attachment1 = self.attachment.attach(
            doc, self.test_user, self.revision
        )
        self.assertEqual(DocumentAttachment.objects.count(), 1)
        self.assertEqual(document_attachment1.file, self.attachment)
        self.assertTrue(document_attachment1.is_original)
        self.assertEqual(document_attachment1.name, self.revision.filename)
        self.assertEqual(document_attachment1.attached_by, self.test_user)

        document_attachment2 = self.attachment.attach(
            doc, self.test_user, self.revision2
        )
        self.assertEqual(DocumentAttachment.objects.count(), 1)
        self.assertEqual(document_attachment2.file, self.attachment)
        self.assertTrue(document_attachment2.is_original)
        self.assertEqual(document_attachment2.name, self.revision2.filename)
        self.assertEqual(document_attachment2.attached_by, self.test_user)
        self.assertEqual(document_attachment1.pk, document_attachment2.pk)

    def test_trash_revision(self):
        self.assertEqual(TrashedAttachment.objects.count(), 0)
        trashed_attachment = self.revision2.trash()
        self.assertEqual(TrashedAttachment.objects.count(), 1)
        self.assertEqual(trashed_attachment.file, self.attachment.current_revision.file)
        self.assertEqual(trashed_attachment.trashed_by, "unknown")
        self.assertTrue(trashed_attachment.was_current)
        # the attachment revision wasn't really deleted,
        # only a trash item created
        self.assertTrue(AttachmentRevision.objects.filter(pk=self.revision.pk).exists())

    def test_trash_revision_with_username(self):
        self.assertTrue(self.storage.exists(self.revision.file.name))
        trashed_attachment = self.revision.trash(username="trasher")
        self.assertEqual(TrashedAttachment.objects.count(), 1)
        self.assertEqual(trashed_attachment.trashed_by, "trasher")
        self.assertTrue(self.storage.exists(self.revision.file.name))

    def test_delete_revision_directly(self):
        # deleting a revision without providing information
        # still creates a trashedattachment item and leaves file in place
        pk = self.revision2.pk
        self.assertTrue(self.storage.exists(self.revision.file.name))
        trashed_attachment = self.revision2.delete()
        self.assertTrue(trashed_attachment)
        self.assertFalse(AttachmentRevision.objects.filter(pk=pk).exists())
        self.assertTrue(self.storage.exists(self.revision.file.name))

    def test_first_trash_then_delete_revision(self):
        pk = self.revision.pk
        trashed_attachment = self.revision.delete(username="trasher")
        self.assertTrue(trashed_attachment)
        self.assertFalse(AttachmentRevision.objects.filter(pk=pk).exists())

    def test_deleting_trashed_item(self):
        pk = self.revision2.pk
        path = self.revision2.file.name
        trashed_attachment = self.revision2.delete(username="trasher")
        self.assertTrue(trashed_attachment)
        self.assertFalse(AttachmentRevision.objects.filter(pk=pk).exists())
        self.assertTrue(self.storage.exists(path))
        trashed_attachment.delete()
        self.assertFalse(self.storage.exists(path))

    def test_delete_revision(self):
        # adding a new revision sets the current revision automatically
        self.assertTrue(self.attachment.current_revision, self.revision2)

        # deleting it again resets the current revision to the previous
        self.revision2.delete()
        self.assertTrue(self.attachment.current_revision, self.revision)

        # deleting the only revision left raises an IntegrityError exception
        self.assertRaises(IntegrityError, self.revision.delete)
