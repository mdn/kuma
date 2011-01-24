from notifications.models import Watch, WatchFilter
from users.tests import user


def watch(save=False, **kwargs):
    # TODO: better defaults, when there are events available.
    defaults = {'user': kwargs.get('user') or user()}
    defaults.update(kwargs)
    w = Watch.objects.create(**defaults)
    if save:
        w.save()
    return w


def watch_filter(save=False, **kwargs):
    defaults = {'watch': kwargs.get('watch') or watch(),
                'name': 'test',
                'value': 1234}
    defaults.update(kwargs)
    f = WatchFilter.objects.create(**defaults)
    if save:
        f.save()
    return f
