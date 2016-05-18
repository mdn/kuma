from datetime import date, timedelta

from django.test import TestCase

from kuma.core.tests import eq_
from ..models import IPBan


class RevisionIPTests(TestCase):
    def test_delete_older_than_default_30_days(self):
        old_date = date.today() - timedelta(days=31)
        IPBan(ip='127.0.0.1', created=old_date).save()
        eq_(1, IPBan.objects.count())
        IPBan.objects.delete_old()
        eq_(0, IPBan.objects.count())

    def test_delete_older_than_days_argument(self):
        ban_date = date.today() - timedelta(days=5)
        IPBan(ip='127.0.0.1', created=ban_date).save()
        eq_(1, IPBan.objects.count())
        IPBan.objects.delete_old(days=4)
        eq_(0, IPBan.objects.count())

    def test_delete_older_than_only_deletes_older_than(self):
        oldest_date = date.today() - timedelta(days=31)
        IPBan(ip='127.0.0.1', created=oldest_date).save()

        old_date = date.today() - timedelta(days=29)
        IPBan(ip='127.0.0.2', created=old_date).save()

        now_date = date.today()
        IPBan(ip='127.0.0.3', created=now_date).save()
        eq_(3, IPBan.objects.count())
        IPBan.objects.delete_old()
        eq_(2, IPBan.objects.count())
