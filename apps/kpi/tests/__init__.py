# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

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
