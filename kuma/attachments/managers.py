from django.db import models


class AttachmentManager(models.Manager):
    def allow_add_attachment_by(self, user):
        """Returns whether the `user` is allowed to upload attachments.

        This is determined by a negative permission, `disallow_add_attachment`
        When the user has this permission, upload is disallowed unless it's
        a superuser or staff.
        """
        if user.is_superuser or user.is_staff:
            # Superusers and staff always allowed
            return True
        if user.has_perm('attachments.add_attachment'):
            # Explicit add permission overrides disallow
            return True
        if user.has_perm('attachments.disallow_add_attachment'):
            # Disallow generally applied via group, so per-user allow can
            # override
            return False
        return True
