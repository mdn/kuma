from datetime import date

from kpi.models import MetricKind, Metric


def metric_kind(**kwargs):
    mk = MetricKind(code=kwargs.get('code', 'something'))
    mk.save()
    return mk

def metric(**kwargs):
    defaults = {'start': date(1980, 02, 16),
                'end': date(1980, 02, 23),
                'value': 33}
    if 'kind' not in kwargs:
        defaults['kind'] = metric_kind(save=True)
    defaults.update(kwargs)
    m = Metric(**defaults)
    return m
