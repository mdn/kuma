import calendar
import hashlib
from datetime import datetime

from constance import config
from django.conf import settings
from django.utils import timezone
from django.utils.http import http_date

from kuma.core.urlresolvers import reverse


def allow_add_attachment_by(user):
    """Returns whether the `user` is allowed to upload attachments.

    This is determined by a negative permission, `disallow_add_attachment`
    When the user has this permission, upload is disallowed unless it's
    a superuser or staff.
    """
    if config.WIKI_ATTACHMENTS_DISABLE_UPLOAD:
        # Uploading via the Wiki is disabled
        return False
    if user.is_superuser or user.is_staff:
        # Superusers and staff always allowed
        return True
    if user.has_perm("attachments.add_attachment"):
        # Explicit add permission overrides disallow
        return True
    if user.has_perm("attachments.disallow_add_attachment"):
        # Disallow generally applied via group, so per-user allow can
        # override
        return False
    return True


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
