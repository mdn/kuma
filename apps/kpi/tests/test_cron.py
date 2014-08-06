from datetime import date
import time

from nose.tools import eq_

from kpi.cron import update_l10n_metric
from kpi.models import Metric, L10N_METRIC_CODE
from kpi.tests import metric_kind
from kuma.wiki.tests import document, revision
from sumo.tests import TestCase


class CronJobTests(TestCase):

    fixtures = ['test_users.json']

    def test_update_l10n_metric_cron(self):
        """Verify the cron job creates the correct metric."""
        l10n_kind = metric_kind(code=L10N_METRIC_CODE, save=True)

        # Create the en-US document with an approved revision.
        doc = document(save=True)
        rev = revision(
            document=doc,
            is_approved=True,
            save=True)

        time.sleep(1)

        # Create an es translation
        es_doc = document(parent=doc, locale='es', save=True)
        revision(
            document=es_doc,
            is_approved=True,
            based_on=rev,
            save=True)

        # Run it and verify results.
        # Value should be 100%
        update_l10n_metric()
        metrics = Metric.objects.filter(kind=l10n_kind)
        eq_(1, len(metrics))
        eq_(100, metrics[0].value)

        # Update the en-US document
        rev2 = revision(
            document=doc,
            is_approved=True,
            save=True)

        # Run it and verify results.
        # Value should be 0%
        update_l10n_metric()
        metrics = Metric.objects.filter(kind=l10n_kind)
        eq_(1, len(metrics))
        eq_(0, metrics[0].value)

        time.sleep(1)

        # Create a pt-BR translation
        ptBR_doc = document(parent=doc, locale='pt-BR', save=True)
        revision(
            document=ptBR_doc,
            is_approved=True,
            based_on=rev,
            save=True)

        # Run it and verify results.
        # Value should be 50%
        update_l10n_metric()
        metrics = Metric.objects.filter(kind=l10n_kind)
        eq_(1, len(metrics))
        eq_(50, metrics[0].value)
