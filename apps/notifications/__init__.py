from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError

from .models import EventWatch


def create_watch(kls, id, email):
    """
    Start watching an object. If already watching, returns False.
    """

    # Check that this object exists, or raise DNE.
    kls.objects.get(pk=id)

    ct = ContentType.objects.get_for_model(kls)
    try:
        e = EventWatch(content_type=ct, watch_id=id, email=email)
        e.save()
        return True
    except IntegrityError:
        return False


def check_watch(kls, id, email):
    """
    Check whether an email address is watching an object.
    """

    ct = ContentType.objects.get_for_model(kls)

    try:
        EventWatch.uncached.get(content_type=ct, watch_id=id, email=email)
        return True
    except EventWatch.DoesNotExist:
        return False


def destroy_watch(kls, id, email):
    """
    Destroy a watch on an object. If watch does not exist, return False.
    """

    ct = ContentType.objects.get_for_model(kls)

    try:
        w = EventWatch.objects.get(content_type=ct, watch_id=id, email=email)
        w.delete()
        return True
    except EventWatch.DoesNotExist:
        return False
