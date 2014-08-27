from datetime import date, timedelta

import cronjobs

from kpi.models import Metric, MetricKind, L10N_METRIC_CODE
from kuma.wiki.models import Document


@cronjobs.register
def update_l10n_metric():
    """Calculate new l10n coverage numbers and save.

    We don't enforce l10n completeness, so coverage is the % of translated docs
    that are modified AFTER the most recent edit to their en-US source.
    """
    up_to_date_translations = 0
    translations = Document.objects.exclude(locale='en-US')
    for translation in translations:
        if (hasattr(translation, 'modified') and
            hasattr(translation.parent, 'modified') and
            translation.modified > translation.parent.modified):
            up_to_date_translations += 1

    coverage = up_to_date_translations / float(translations.count())

    # Save the value to Metric table.
    metric_kind = MetricKind.objects.get(code=L10N_METRIC_CODE)
    start = date.today()
    end = start + timedelta(days=1)
    metric, created = Metric.objects.get_or_create(kind=metric_kind,
                                                   start=start,
                                                   end=end)
    metric.value = int(coverage * 100)  # store as a % int
    metric.save()
