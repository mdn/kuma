import calendar
import hashlib
from datetime import datetime

from django.conf import settings
from django.utils import timezone
from django.utils.http import http_date

from kuma.core.urlresolvers import reverse


def full_attachment_url(attachment_id, filename):
    path = reverse(
        "attachments.raw_file",
        kwargs={"attachment_id": attachment_id, "filename": filename},
    )
    return f"{settings.PROTOCOL}{settings.ATTACHMENT_HOST}{path}"


def convert_to_utc(dt):
    """
    Given a timezone naive or aware datetime return it converted to UTC.
    """
    # Check if the given dt is timezone aware and if not make it aware.
    if timezone.is_naive(dt):
        default_timezone = timezone.get_default_timezone()
        dt = timezone.make_aware(dt, default_timezone)

    # Convert the datetime to UTC.
    return dt.astimezone(timezone.utc)


def convert_to_http_date(dt):
    """
    Given a timezone naive or aware datetime return the HTTP date-formatted
    string to be used in HTTP response headers.
    """
    # Convert the datetime to UTC.
    utc_dt = convert_to_utc(dt)
    # Convert the UTC datetime to seconds since the epoch.
    epoch_dt = calendar.timegm(utc_dt.utctimetuple())
    # Format the thing as a RFC1123 datetime.
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
        "date": now.strftime("%Y/%m/%d"),
        "id": instance.attachment.id,
        "md5": hashlib.md5(str(now).encode()).hexdigest(),
        "filename": filename,
    }
