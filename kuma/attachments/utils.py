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
    """Generate a path to store a file attachment."""
    # TODO: We could probably just get away with strftime formatting
    # in the 'upload_to' argument here, but this does a bit more to be
    # extra-safe with potential duplicate filenames.
    #
    # For now, the filesystem storage path will look like this:
    #
    # attachments/year/month/day/attachment_id/md5/filename
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


def attachments_json(attachments):
    """
    Given a list of Attachments (e.g., from a Document), make some
    nice JSON out of them for easy display.

    """
    attachments_list = []
    for attachment in attachments:
        obj = {
            'title': attachment.title,
            'date': str(attachment.current_revision.created),
            'description': attachment.current_revision.description,
            'url': attachment.get_file_url(),
            'size': 0,
            'creator': attachment.current_revision.creator.username,
            'creator_url': attachment.current_revision.creator.get_absolute_url(),
            'revision': attachment.current_revision.id,
            'id': attachment.id,
            'mime': attachment.current_revision.mime_type
        }
        # Adding this to prevent "UnicodeEncodeError" for certain media
        try:
            obj['size'] = attachment.current_revision.file.size
        except:
            pass

        obj['html'] = mark_safe(loader.render_to_string('attachments/includes/attachment_row.html',
                                                        {'attachment': obj}))
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
