from nose.tools import ok_

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from kuma.core.tests import KumaTestCase
from kuma.users.tests import user
from ..models import Attachment


class AttachmentTests(KumaTestCase):
    def test_permissions(self):
        """Ensure that the negative and positive permissions for adding
        attachments work."""
        # Get the negative and positive permissions
        ct = ContentType.objects.get(app_label='attachments', model='attachment')
        p1 = Permission.objects.get(codename='disallow_add_attachment',
                                    content_type=ct)
        p2 = Permission.objects.get(codename='add_attachment',
                                    content_type=ct)

        # Create a group with the negative permission.
        g1, created = Group.objects.get_or_create(name='cannot_attach')
        g1.permissions = [p1]
        g1.save()

        # Create a group with the positive permission.
        g2, created = Group.objects.get_or_create(name='can_attach')
        g2.permissions = [p2]
        g2.save()

        # User with no explicit permission is allowed
        u2 = user(username='test_user2', save=True)
        ok_(Attachment.objects.allow_add_attachment_by(u2))

        # User in group with negative permission is disallowed
        u3 = user(username='test_user3', save=True)
        u3.groups = [g1]
        u3.save()
        ok_(not Attachment.objects.allow_add_attachment_by(u3))

        # Superusers can do anything, despite group perms
        u1 = user(username='test_super', is_superuser=True, save=True)
        u1.groups = [g1]
        u1.save()
        ok_(Attachment.objects.allow_add_attachment_by(u1))

        # User with negative permission is disallowed
        u4 = user(username='test_user4', save=True)
        u4.user_permissions.add(p1)
        u4.save()
        ok_(not Attachment.objects.allow_add_attachment_by(u4))

        # User with positive permission overrides group
        u5 = user(username='test_user5', save=True)
        u5.groups = [g1]
        u5.user_permissions.add(p2)
        u5.save()
        ok_(Attachment.objects.allow_add_attachment_by(u5))

        # Group with positive permission takes priority
        u6 = user(username='test_user6', save=True)
        u6.groups = [g1, g2]
        u6.save()
        ok_(Attachment.objects.allow_add_attachment_by(u6))

        # positive permission takes priority, period.
        u7 = user(username='test_user7', save=True)
        u7.user_permissions.add(p1)
        u7.user_permissions.add(p2)
        u7.save()
        ok_(Attachment.objects.allow_add_attachment_by(u7))
