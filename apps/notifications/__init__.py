from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError

from .models import EventWatch


def create_watch(kls, id, email, event_type):
    """Start watching an object. If already watching, returns False."""

    # Check that this object exists, or raise DNE.
    kls.objects.get(pk=id)

    ct = ContentType.objects.get_for_model(kls)
    try:
        e = EventWatch(content_type=ct, watch_id=id, email=email,
                       event_type=event_type)
        e.save()
        return True
    except IntegrityError:
        return False


def check_watch(kls, id, email, event_type=None):
    """Check whether an email address is watching an object."""

    ct = ContentType.objects.get_for_model(kls)

    try:
        kwargs = {'content_type': ct, 'watch_id': id, 'email': email}
        if event_type:
            kwargs['event_type'] = event_type
        EventWatch.uncached.get(**kwargs)
        return True
    except EventWatch.DoesNotExist:
        return False


def destroy_watch(kls, id, email, event_type=None):
    """Destroy a watch on an object. If watch does not exist, return False."""

    ct = ContentType.objects.get_for_model(kls)

    kwargs = {'content_type': ct, 'watch_id': id, 'email': email}
    if event_type:
        kwargs['event_type'] = event_type
    w = EventWatch.objects.filter(**kwargs)
    count = w.count()
    w.delete()
    return count > 0
