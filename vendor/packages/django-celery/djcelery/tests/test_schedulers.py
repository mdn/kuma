from __future__ import absolute_import

from datetime import datetime, timedelta
from itertools import count
from time import time

from celery.schedules import schedule, crontab
from celery.utils.timeutils import timedelta_seconds

from djcelery import schedulers
from djcelery.app import app
from djcelery.models import PeriodicTask, IntervalSchedule, CrontabSchedule
from djcelery.models import PeriodicTasks
from djcelery.utils import now
from djcelery.tests.utils import unittest


def create_model_interval(schedule, **kwargs):
    return create_model(interval=IntervalSchedule.from_schedule(schedule),
                        **kwargs)


def create_model_crontab(schedule, **kwargs):
    return create_model(crontab=CrontabSchedule.from_schedule(schedule),
                        **kwargs)

_next_id = count(0).next


def create_model(Model=PeriodicTask, **kwargs):
    entry = dict(name="thefoo%s" % _next_id(),
                 task="djcelery.unittest.add%s" % _next_id(),
                 args="[2, 2]",
                 kwargs='{"callback": "foo"}',
                 queue="xaz",
                 routing_key="cpu",
                 exchange="foo")
    return Model(**dict(entry, **kwargs))


class EntryTrackSave(schedulers.ModelEntry):

    def __init__(self, *args, **kwargs):
        self.saved = 0
        super(EntryTrackSave, self).__init__(*args, **kwargs)

    def save(self):
        self.saved += 1
        super(EntryTrackSave, self).save()


class EntrySaveRaises(schedulers.ModelEntry):

    def save(self):
        raise RuntimeError("this is expected")


class TrackingScheduler(schedulers.DatabaseScheduler):
    Entry = EntryTrackSave

    def __init__(self, *args, **kwargs):
        self.flushed = 0
        schedulers.DatabaseScheduler.__init__(self, *args, **kwargs)

    def sync(self):
        self.flushed += 1
        schedulers.DatabaseScheduler.sync(self)


class test_ModelEntry(unittest.TestCase):
    Entry = EntryTrackSave

    def tearDown(self):
        PeriodicTask.objects.all().delete()

    def test_entry(self):
        m = create_model_interval(schedule(timedelta(seconds=10)))
        e = self.Entry(m)

        self.assertListEqual(e.args, [2, 2])
        self.assertDictEqual(e.kwargs, {"callback": "foo"})
        self.assertTrue(e.schedule)
        self.assertEqual(e.total_run_count, 0)
        self.assertIsInstance(e.last_run_at, datetime)
        self.assertDictContainsSubset({"queue": "xaz",
                                       "exchange": "foo",
                                       "routing_key": "cpu"}, e.options)

        right_now = now()
        m2 = create_model_interval(schedule(timedelta(seconds=10)),
                                   last_run_at=right_now)
        self.assertTrue(m2.last_run_at)
        e2 = self.Entry(m2)
        self.assertIs(e2.last_run_at, right_now)

        e3 = e2.next()
        self.assertGreater(e3.last_run_at, e2.last_run_at)
        self.assertEqual(e3.total_run_count, 1)


class test_DatabaseScheduler(unittest.TestCase):
    Scheduler = TrackingScheduler

    def setUp(self):
        PeriodicTask.objects.all().delete()
        self.prev_schedule = app.conf.CELERYBEAT_SCHEDULE
        app.conf.CELERYBEAT_SCHEDULE = {}
        m1 = create_model_interval(schedule(timedelta(seconds=10)))
        m2 = create_model_interval(schedule(timedelta(minutes=20)))
        m3 = create_model_crontab(crontab(minute="2,4,5", nowfun=now))
        for obj in m1, m2, m3:
            obj.save()
        self.s = self.Scheduler()
        self.m1 = PeriodicTask.objects.get(name=m1.name)
        self.m2 = PeriodicTask.objects.get(name=m2.name)
        self.m3 = PeriodicTask.objects.get(name=m3.name)

    def tearDown(self):
        app.conf.CELERYBEAT_SCHEDULE = self.prev_schedule
        PeriodicTask.objects.all().delete()

    def test_constructor(self):
        self.assertIsInstance(self.s._dirty, set)
        self.assertIsNone(self.s._last_sync)
        self.assertTrue(self.s.sync_every)

    def test_all_as_schedule(self):
        sched = self.s.schedule
        self.assertTrue(sched)
        self.assertEqual(len(sched), 4)
        self.assertIn("celery.backend_cleanup", sched)
        for n, e in sched.items():
            self.assertIsInstance(e, self.s.Entry)

    def test_schedule_changed(self):
        self.m2.args = "[16, 16]"
        self.m2.save()
        e2 = self.s.schedule[self.m2.name]
        self.assertListEqual(e2.args, [16, 16])

        self.m1.args = "[32, 32]"
        self.m1.save()
        e1 = self.s.schedule[self.m1.name]
        self.assertListEqual(e1.args, [32, 32])
        e1 = self.s.schedule[self.m1.name]
        self.assertListEqual(e1.args, [32, 32])

        self.m3.delete()
        self.assertRaises(KeyError, self.s.schedule.__getitem__, self.m3.name)

    def test_should_sync(self):
        self.assertTrue(self.s.should_sync())
        self.s._last_sync = time()
        self.assertFalse(self.s.should_sync())
        self.s._last_sync -= self.s.sync_every
        self.assertTrue(self.s.should_sync())

    def test_reserve(self):
        e1 = self.s.schedule[self.m1.name]
        self.s.schedule[self.m1.name] = self.s.reserve(e1)
        self.assertEqual(self.s.flushed, 2)

        e2 = self.s.schedule[self.m2.name]
        self.s.schedule[self.m2.name] = self.s.reserve(e2)
        self.assertEqual(self.s.flushed, 2)
        self.assertIn(self.m2.name, self.s._dirty)

    def test_sync_saves_last_run_at(self):
        e1 = self.s.schedule[self.m2.name]
        last_run = e1.last_run_at
        last_run2 = last_run - timedelta(days=1)
        e1.model.last_run_at = last_run2
        self.s._dirty.add(self.m2.name)
        self.s.sync()

        e2 = self.s.schedule[self.m2.name]
        self.assertEqual(e2.last_run_at, last_run2)

    def test_sync_syncs_before_save(self):

        # Get the entry for m2
        e1 = self.s.schedule[self.m2.name]

        # Increment the entry (but make sure it doesn't sync)
        self.s._last_sync = time()
        e2 = self.s.schedule[e1.name] = self.s.reserve(e1)
        self.assertEqual(self.s.flushed, 2)

        # Fetch the raw object from db, change the args
        # and save the changes.
        m2 = PeriodicTask.objects.get(pk=self.m2.pk)
        m2.args = "[16, 16]"
        m2.save()

        # get_schedule should now see the schedule has changed.
        # and also sync the dirty objects.
        e3 = self.s.schedule[self.m2.name]
        self.assertEqual(self.s.flushed, 3)
        self.assertEqual(e3.last_run_at, e2.last_run_at)
        self.assertListEqual(e3.args, [16, 16])

    def test_sync_not_dirty(self):
        self.s._dirty.clear()
        self.s.sync()

    def test_sync_object_gone(self):
        self.s._dirty.add("does-not-exist")
        self.s.sync()

    def test_sync_rollback_on_save_error(self):
        self.s.schedule[self.m1.name] = EntrySaveRaises(self.m1)
        self.s._dirty.add(self.m1.name)
        self.assertRaises(RuntimeError, self.s.sync)


class test_models(unittest.TestCase):

    def test_IntervalSchedule_unicode(self):
        self.assertEqual(unicode(IntervalSchedule(every=1, period="seconds")),
                         "every second")
        self.assertEqual(unicode(IntervalSchedule(every=10, period="seconds")),
                         "every 10 seconds")

    def test_CrontabSchedule_unicode(self):
        self.assertEqual(unicode(CrontabSchedule(minute=3,
                                                 hour=3,
                                                 day_of_week=None)),
                         "3 3 * (m/h/d)")
        self.assertEqual(unicode(CrontabSchedule(minute=3,
                                                 hour=3,
                                                 day_of_week=None)),
                         "3 3 * (m/h/d)")

    def test_PeriodicTask_unicode_interval(self):
        p = create_model_interval(schedule(timedelta(seconds=10)))
        self.assertEqual(unicode(p),
                        "%s: every 10.0 seconds" % p.name)

    def test_PeriodicTask_unicode_crontab(self):
        p = create_model_crontab(crontab(hour="4, 5", day_of_week="4, 5",
                                 nowfun=now))
        self.assertEqual(unicode(p),
                        "%s: * 4,5 4,5 (m/h/d)" % p.name)

    def test_PeriodicTask_schedule_property(self):
        p1 = create_model_interval(schedule(timedelta(seconds=10)))
        s1 = p1.schedule
        self.assertEqual(timedelta_seconds(s1.run_every), 10)

        p2 = create_model_crontab(crontab(hour="4, 5", minute="10,20,30",
                                          nowfun=now))
        s2 = p2.schedule
        self.assertSetEqual(s2.hour, set([4, 5]))
        self.assertSetEqual(s2.minute, set([10, 20, 30]))
        self.assertSetEqual(s2.day_of_week, set([0, 1, 2, 3, 4, 5, 6]))

    def test_PeriodicTask_unicode_no_schedule(self):
        p = create_model()
        self.assertEqual(unicode(p), "%s: {no schedule}" % p.name)

    def test_CrontabSchedule_schedule(self):
        s = CrontabSchedule(minute="3, 7", hour="3, 4", day_of_week="*")
        self.assertEqual(s.schedule.minute, set([3, 7]))
        self.assertEqual(s.schedule.hour, set([3, 4]))
        self.assertEqual(s.schedule.day_of_week, set([0, 1, 2, 3, 4, 5, 6]))


class test_model_PeriodicTasks(unittest.TestCase):

    def setUp(self):
        PeriodicTasks.objects.all().delete()

    def test_track_changes(self):
        self.assertIsNone(PeriodicTasks.last_change())
        m1 = create_model_interval(schedule(timedelta(seconds=10)))
        m1.save()
        x = PeriodicTasks.last_change()
        self.assertTrue(x)
        m1.args = "(23, 24)"
        m1.save()
        y = PeriodicTasks.last_change()
        self.assertTrue(y)
        self.assertGreater(y, x)
