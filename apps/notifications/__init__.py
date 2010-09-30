from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError

from .models import EventWatch


def create_watch(kls, id, email, event_type, locale=''):
    """Start watching an object. If already watching, returns False."""

    if id != None and not kls.objects.filter(pk=id).exists():
        raise kls.DoesNotExist

    ct = ContentType.objects.get_for_model(kls)
    try:
        e = EventWatch(content_type=ct, watch_id=id, email=email,
                       event_type=event_type, locale=locale)
        e.save()
        return True
    except IntegrityError:
        return False


def check_watch(kls, id, email, event_type=None, locale=''):
    """Check whether an email address is watching an object."""

    ct = ContentType.objects.get_for_model(kls)

    kwargs = {'content_type': ct, 'watch_id': id, 'email': email,
              'locale': locale}
    if event_type:
        kwargs['event_type'] = event_type
    return EventWatch.uncached.filter(**kwargs).exists()


def destroy_watch(kls, id, email, event_type=None, locale=''):
    """Destroy a watch on an object. If watch does not exist, return False."""

    ct = ContentType.objects.get_for_model(kls)

    kwargs = {'content_type': ct, 'watch_id': id, 'email': email,
              'locale': locale}
    if event_type:
        kwargs['event_type'] = event_type
    w = EventWatch.objects.filter(**kwargs)
    count = w.count()
    w.delete()
    return count > 0
