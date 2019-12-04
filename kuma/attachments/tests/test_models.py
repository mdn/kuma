import datetime

from constance.test import override_config
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.files.base import ContentFile
from django.db.utils import IntegrityError

from kuma.users.tests import user, UserTestCase
from kuma.wiki.models import DocumentAttachment
from kuma.wiki.tests import document

from ..models import Attachment, AttachmentRevision, TrashedAttachment
from ..utils import allow_add_attachment_by


class AttachmentModelTests(UserTestCase):

    def setUp(self):
        super(AttachmentModelTests, self).setUp()
        self.test_user = self.user_model.objects.get(username='testuser2')
        self.attachment = Attachment(title='some title')
        self.attachment.save()
        self.revision = AttachmentRevision(
            attachment=self.attachment,
            mime_type='text/plain',
            title=self.attachment.title,
            description='some description',
            created=datetime.datetime.now(),
            is_approved=True)
        self.revision.creator = self.test_user
        self.revision.file.save('filename.txt',
                                ContentFile(b'Meh meh I am a test file.'))

        self.revision2 = AttachmentRevision(
            attachment=self.attachment,
            mime_type='text/plain',
            title=self.attachment.title,
            description='some description',
            created=datetime.datetime.now(),
            is_approved=True)
        self.revision2.creator = self.test_user
        self.revision2.file.save('filename2.txt',
                                 ContentFile(b'Meh meh I am a test file.'))
        self.storage = AttachmentRevision.file.field.storage

    def test_document_attachment(self):
        doc = document(save=True)
        self.assertEqual(DocumentAttachment.objects.count(), 0)

        document_attachment1 = self.attachment.attach(
            doc, self.test_user, self.revision)
        self.assertEqual(DocumentAttachment.objects.count(), 1)
        self.assertEqual(document_attachment1.file, self.attachment)
        self.assertTrue(document_attachment1.is_original)
        self.assertEqual(document_attachment1.name, self.revision.filename)
        self.assertEqual(document_attachment1.attached_by, self.test_user)

        document_attachment2 = self.attachment.attach(
            doc, self.test_user, self.revision2)
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
        self.assertEqual(trashed_attachment.file,
                         self.attachment.current_revision.file)
        self.assertEqual(trashed_attachment.trashed_by, 'unknown')
        self.assertTrue(trashed_attachment.was_current)
        # the attachment revision wasn't really deleted,
        # only a trash item created
        self.assertTrue(AttachmentRevision.objects.filter(pk=self.revision.pk)
                                                  .exists())

    def test_trash_revision_with_username(self):
        self.assertTrue(self.storage.exists(self.revision.file.name))
        trashed_attachment = self.revision.trash(username='trasher')
        self.assertEqual(TrashedAttachment.objects.count(), 1)
        self.assertEqual(trashed_attachment.trashed_by, 'trasher')
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
        trashed_attachment = self.revision.delete(username='trasher')
        self.assertTrue(trashed_attachment)
        self.assertFalse(AttachmentRevision.objects.filter(pk=pk).exists())

    def test_deleting_trashed_item(self):
        pk = self.revision2.pk
        path = self.revision2.file.name
        trashed_attachment = self.revision2.delete(username='trasher')
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

    def test_permissions(self):
        """
        Ensure that the negative and positive permissions for adding
        attachments work.
        """
        # Get the negative and positive permissions
        ct = ContentType.objects.get(app_label='attachments',
                                     model='attachment')
        p1 = Permission.objects.get(codename='disallow_add_attachment',
                                    content_type=ct)
        p2 = Permission.objects.get(codename='add_attachment',
                                    content_type=ct)

        # Create a group with the negative permission.
        g1, created = Group.objects.get_or_create(name='cannot_attach')
        g1.permissions.set([p1])
        g1.save()

        # Create a group with the positive permission.
        g2, created = Group.objects.get_or_create(name='can_attach')
        g2.permissions.set([p2])
        g2.save()

        # User with no explicit permission is allowed
        u2 = user(username='test_user2', save=True)
        self.assertTrue(allow_add_attachment_by(u2))

        # User in group with negative permission is disallowed
        u3 = user(username='test_user3', save=True)
        u3.groups.set([g1])
        u3.save()
        self.assertTrue(not allow_add_attachment_by(u3))

        # Superusers can do anything, despite group perms
        u1 = user(username='test_super', is_superuser=True, save=True)
        u1.groups.set([g1])
        u1.save()
        self.assertTrue(allow_add_attachment_by(u1))

        # User with negative permission is disallowed
        u4 = user(username='test_user4', save=True)
        u4.user_permissions.add(p1)
        u4.save()
        self.assertTrue(not allow_add_attachment_by(u4))

        # User with positive permission overrides group
        u5 = user(username='test_user5', save=True)
        u5.groups.set([g1])
        u5.user_permissions.add(p2)
        u5.save()
        self.assertTrue(allow_add_attachment_by(u5))

        # Group with positive permission takes priority
        u6 = user(username='test_user6', save=True)
        u6.groups.set([g1, g2])
        u6.save()
        self.assertTrue(allow_add_attachment_by(u6))

        # positive permission takes priority, period.
        u7 = user(username='test_user7', save=True)
        u7.user_permissions.add(p1)
        u7.user_permissions.add(p2)
        u7.save()
        self.assertTrue(allow_add_attachment_by(u7))

    @override_config(WIKI_ATTACHMENTS_DISABLE_UPLOAD=True)
    def test_permissions_when_disabled(self):
        # All users, including superusers, are denied
        admin = self.user_model.objects.get(username='admin')
        self.assertFalse(allow_add_attachment_by(admin))
