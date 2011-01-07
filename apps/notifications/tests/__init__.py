from notifications.models import Watch, WatchFilter
from sumo.tests import get_user


def watch(**kwargs):
    u = kwargs.get('user') or get_user()

    # TODO: better defaults, when there are events available.
    defaults = {'user': u}
    defaults.update(kwargs)

    return Watch.objects.create(**defaults)


def watch_filter(**kwargs):
    w = None
    if 'watch' not in kwargs:
        w = watch()

    defaults = {'watch': w, 'name': 'test', 'value': 1234}
    defaults.update(kwargs)

    return WatchFilter.objects.create(**defaults)
