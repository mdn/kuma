from datetime import date, timedelta

from django.test import TestCase

from ..models import IPBan


class RevisionIPTests(TestCase):
    def test_delete_older_than_default_30_days(self):
        old_date = date.today() - timedelta(days=31)
        IPBan(ip="127.0.0.1", created=old_date).save()
        assert 1 == IPBan.objects.count()
        IPBan.objects.delete_old()
        assert 0 == IPBan.objects.count()

    def test_delete_older_than_days_argument(self):
        ban_date = date.today() - timedelta(days=5)
        IPBan(ip="127.0.0.1", created=ban_date).save()
        assert 1 == IPBan.objects.count()
        IPBan.objects.delete_old(days=4)
        assert 0 == IPBan.objects.count()

    def test_delete_older_than_only_deletes_older_than(self):
        oldest_date = date.today() - timedelta(days=31)
        IPBan(ip="127.0.0.1", created=oldest_date).save()

        old_date = date.today() - timedelta(days=29)
        IPBan(ip="127.0.0.2", created=old_date).save()

        now_date = date.today()
        IPBan(ip="127.0.0.3", created=now_date).save()
        assert 3 == IPBan.objects.count()
        IPBan.objects.delete_old()
        assert 2 == IPBan.objects.count()
