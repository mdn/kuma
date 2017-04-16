from __future__ import absolute_import

from django.test.testcases import TestCase as DjangoTestCase

from someapp.models import Thing
from someapp.tasks import SomeModelTask


class SimpleTest(DjangoTestCase):

    def setUp(self):
        self.thing = Thing.objects.create(name=u"Foo")

    def test_apply_task(self):
        "Apply task function."
        result = SomeModelTask.apply(kwargs={'pk': self.thing.pk})
        self.assertEqual(result.get(), self.thing.name)

    def test_task_function(self):
        "Run task function."
        result = SomeModelTask(pk=self.thing.pk)
        self.assertEqual(result, self.thing.name)
