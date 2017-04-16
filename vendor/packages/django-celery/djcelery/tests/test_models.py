from __future__ import absolute_import

from datetime import datetime, timedelta

from celery import current_app
from celery import states
from celery.utils import gen_unique_id

from djcelery.models import TaskMeta, TaskSetMeta
from djcelery.tests.utils import unittest
from djcelery.utils import now


class TestModels(unittest.TestCase):

    def createTaskMeta(self):
        id = gen_unique_id()
        taskmeta, created = TaskMeta.objects.get_or_create(task_id=id)
        return taskmeta

    def createTaskSetMeta(self):
        id = gen_unique_id()
        tasksetmeta, created = TaskSetMeta.objects.get_or_create(taskset_id=id)
        return tasksetmeta

    def test_taskmeta(self):
        m1 = self.createTaskMeta()
        m2 = self.createTaskMeta()
        m3 = self.createTaskMeta()
        self.assertTrue(unicode(m1).startswith("<Task:"))
        self.assertTrue(m1.task_id)
        self.assertIsInstance(m1.date_done, datetime)

        self.assertEqual(TaskMeta.objects.get_task(m1.task_id).task_id,
                m1.task_id)
        self.assertNotEqual(TaskMeta.objects.get_task(m1.task_id).status,
                            states.SUCCESS)
        TaskMeta.objects.store_result(m1.task_id, True, status=states.SUCCESS)
        TaskMeta.objects.store_result(m2.task_id, True, status=states.SUCCESS)
        self.assertEqual(TaskMeta.objects.get_task(m1.task_id).status,
                         states.SUCCESS)
        self.assertEqual(TaskMeta.objects.get_task(m2.task_id).status,
                         states.SUCCESS)

        # Have to avoid save() because it applies the auto_now=True.
        TaskMeta.objects.filter(task_id=m1.task_id).update(
                date_done=now() - timedelta(days=10))

        expired = TaskMeta.objects.get_all_expired(
                    current_app.conf.CELERY_TASK_RESULT_EXPIRES)
        self.assertIn(m1, expired)
        self.assertNotIn(m2, expired)
        self.assertNotIn(m3, expired)

        TaskMeta.objects.delete_expired(
                    current_app.conf.CELERY_TASK_RESULT_EXPIRES)
        self.assertNotIn(m1, TaskMeta.objects.all())

    def test_tasksetmeta(self):
        m1 = self.createTaskSetMeta()
        m2 = self.createTaskSetMeta()
        m3 = self.createTaskSetMeta()
        self.assertTrue(unicode(m1).startswith("<TaskSet:"))
        self.assertTrue(m1.taskset_id)
        self.assertIsInstance(m1.date_done, datetime)

        self.assertEqual(
                TaskSetMeta.objects.restore_taskset(m1.taskset_id).taskset_id,
                m1.taskset_id)

        # Have to avoid save() because it applies the auto_now=True.
        TaskSetMeta.objects.filter(taskset_id=m1.taskset_id).update(
                date_done=now() - timedelta(days=10))

        expired = TaskSetMeta.objects.get_all_expired(
                    current_app.conf.CELERY_TASK_RESULT_EXPIRES)
        self.assertIn(m1, expired)
        self.assertNotIn(m2, expired)
        self.assertNotIn(m3, expired)

        TaskSetMeta.objects.delete_expired(
                current_app.conf.CELERY_TASK_RESULT_EXPIRES)
        self.assertNotIn(m1, TaskSetMeta.objects.all())

        m4 = self.createTaskSetMeta()
        self.assertEqual(
                TaskSetMeta.objects.restore_taskset(m4.taskset_id).taskset_id,
                m4.taskset_id)

        TaskSetMeta.objects.delete_taskset(m4.taskset_id)
        self.assertIsNone(TaskSetMeta.objects.restore_taskset(m4.taskset_id))
