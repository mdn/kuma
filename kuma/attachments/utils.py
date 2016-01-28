import calendar
from datetime import datetime
import hashlib

from django.conf import settings
from django.core.files import temp as tempfile
from django.template import loader
from django.utils import timezone
from django.utils.http import http_date
from django.utils.safestring import mark_safe

from kuma.core.urlresolvers import reverse


def allow_add_attachment_by(user):
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


def full_attachment_url(attachment_id, filename):
    path = reverse('attachments.raw_file', kwargs={
        'attachment_id': attachment_id,
        'filename': filename,
    })
    return '%s%s%s' % (settings.PROTOCOL, settings.ATTACHMENT_HOST, path)


def convert_to_http_date(dt):
    """
    Given a timezone naive or aware datetime return the HTTP date
    formatted string to be used in HTTP response headers.
    """
    # first check if the given dt is timezone aware and if not make it aware
    if timezone.is_naive(dt):
        default_timezone = timezone.get_default_timezone()
        dt = timezone.make_aware(dt, default_timezone)

    # then convert the datetime to UTC (which epoch time is based on)
    utc_dt = dt.astimezone(timezone.utc)
    # convert the UTC time to the seconds since the epch
    epoch_dt = calendar.timegm(utc_dt.utctimetuple())
    # format the thing as a RFC1123 datetime
    return http_date(epoch_dt)


def attachment_upload_to(instance, filename):
    """
    Generate a path to store a file attachment.
    """
    # For now, the filesystem storage path will look like this:
    #
    # attachments/<year>/<month>/<day>/<attachment_id>/<md5>/<filename>
    #
    # The md5 hash here is of the full timestamp, down to the
    # microsecond, of when the path is generated.
    now = datetime.now()
    return "attachments/%(date)s/%(id)s/%(md5)s/%(filename)s" % {
        'date': now.strftime('%Y/%m/%d'),
        'id': instance.attachment.id,
        'md5': hashlib.md5(str(now)).hexdigest(),
        'filename': filename
    }


def attachments_payload(attachments):
    """
    Given a list of Attachments (e.g., from a Document), make some
    nice JSON out of them for easy display.
    """
    attachments_list = []
    for attachment in attachments:
        current_revision = attachment.current_revision
        obj = {
            'title': attachment.title,
            'date': str(current_revision.created),
            'description': current_revision.description,
            'url': attachment.get_file_url(),
            'creator': current_revision.creator.username,
            'creator_url': current_revision.creator.get_absolute_url(),
            'revision': current_revision.id,
            'id': attachment.id,
            'mime': current_revision.mime_type
        }
        # Adding this to prevent "UnicodeEncodeError" for certain media
        try:
            obj['size'] = current_revision.file.size
        except UnicodeEncodeError:
            obj['size'] = 0

        obj['html'] = mark_safe(
            loader.render_to_string('attachments/includes/attachment_row.html',
                                    {'attachment': obj})
        )
        attachments_list.append(obj)
    return attachments_list


def make_test_file(content=None):
    """Create a fake file for testing purposes."""
    if content is None:
        content = 'I am a test file for upload.'
    # Shamelessly stolen from Django's own file-upload tests.
    tdir = tempfile.gettempdir()
    file_for_upload = tempfile.NamedTemporaryFile(suffix=".txt", dir=tdir)
    file_for_upload.write(content)
    file_for_upload.seek(0)
    return file_for_upload
