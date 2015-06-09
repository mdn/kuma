"""Unit tests for django-picklefield."""

from django.test import TestCase
from django.db import models
from django.core import serializers
from picklefield.compat import json
from picklefield.fields import (PickledObjectField, wrap_conflictual_object,
                                dbsafe_encode)


S1 = 'Hello World'
T1 = (1, 2, 3, 4, 5)
L1 = [1, 2, 3, 4, 5]
D1 = {1: 1, 2: 4, 3: 6, 4: 8, 5: 10}
D2 = {1: 2, 2: 4, 3: 6, 4: 8, 5: 10}


class TestingModel(models.Model):
    pickle_field = PickledObjectField()
    compressed_pickle_field = PickledObjectField(compress=True)
    default_pickle_field = PickledObjectField(default=(D1, S1, T1, L1))


class MinimalTestingModel(models.Model):
    pickle_field = PickledObjectField()


class TestCustomDataType(str):
    pass


class PickledObjectFieldTests(TestCase):
    def setUp(self):
        self.testing_data = (D2, S1, T1, L1,
                             TestCustomDataType(S1),
                             MinimalTestingModel)
        return super(PickledObjectFieldTests, self).setUp()

    def testDataIntegrity(self):
        """
        Tests that data remains the same when saved to and fetched from
        the database, whether compression is enabled or not.
        """
        for value in self.testing_data:
            model_test = TestingModel(pickle_field=value,
                compressed_pickle_field=value)
            model_test.save()
            model_test = TestingModel.objects.get(id__exact=model_test.id)
            # Make sure that both the compressed and uncompressed fields return
            # the same data, even thought it's stored differently in the DB.
            self.assertEquals(value, model_test.pickle_field)
            self.assertEquals(value, model_test.compressed_pickle_field)
            # Make sure we can also retrieve the model
            model_test.save()
            model_test.delete()

        # Make sure the default value for default_pickled_field gets stored
        # correctly and that it isn't converted to a string.
        model_test = TestingModel()
        model_test.save()
        model_test = TestingModel.objects.get(id__exact=model_test.id)
        self.assertEquals((D1, S1, T1, L1),
            model_test.default_pickle_field)

    def testLookups(self):
        """
        Tests that lookups can be performed on data once stored in the
        database, whether compression is enabled or not.

        One problem with cPickle is that it will sometimes output
        different streams for the same object, depending on how they are
        referenced. It should be noted though, that this does not happen
        for every object, but usually only with more complex ones.

        >>> from pickle import dumps
        >>> t = ({1: 1, 2: 4, 3: 6, 4: 8, 5: 10}, \
        ... 'Hello World', (1, 2, 3, 4, 5), [1, 2, 3, 4, 5])
        >>> dumps(({1: 1, 2: 4, 3: 6, 4: 8, 5: 10}, \
        ... 'Hello World', (1, 2, 3, 4, 5), [1, 2, 3, 4, 5]))
        "((dp0\nI1\nI1\nsI2\nI4\nsI3\nI6\nsI4\nI8\nsI5\nI10\nsS'Hello World'\np1\n(I1\nI2\nI3\nI4\nI5\ntp2\n(lp3\nI1\naI2\naI3\naI4\naI5\natp4\n."
        >>> dumps(t)
        "((dp0\nI1\nI1\nsI2\nI4\nsI3\nI6\nsI4\nI8\nsI5\nI10\nsS'Hello World'\np1\n(I1\nI2\nI3\nI4\nI5\ntp2\n(lp3\nI1\naI2\naI3\naI4\naI5\natp4\n."
        >>> # Both dumps() are the same using pickle.

        >>> from cPickle import dumps
        >>> t = ({1: 1, 2: 4, 3: 6, 4: 8, 5: 10}, 'Hello World', (1, 2, 3, 4, 5), [1, 2, 3, 4, 5])
        >>> dumps(({1: 1, 2: 4, 3: 6, 4: 8, 5: 10}, 'Hello World', (1, 2, 3, 4, 5), [1, 2, 3, 4, 5]))
        "((dp1\nI1\nI1\nsI2\nI4\nsI3\nI6\nsI4\nI8\nsI5\nI10\nsS'Hello World'\np2\n(I1\nI2\nI3\nI4\nI5\ntp3\n(lp4\nI1\naI2\naI3\naI4\naI5\nat."
        >>> dumps(t)
        "((dp1\nI1\nI1\nsI2\nI4\nsI3\nI6\nsI4\nI8\nsI5\nI10\nsS'Hello World'\n(I1\nI2\nI3\nI4\nI5\nt(lp2\nI1\naI2\naI3\naI4\naI5\natp3\n."
        >>> # But with cPickle the two dumps() are not the same!
        >>> # Both will generate the same object when loads() is called though.

        We can solve this by calling deepcopy() on the value before
        pickling it, as this copies everything to a brand new data
        structure.

        >>> from cPickle import dumps
        >>> from copy import deepcopy
        >>> t = ({1: 1, 2: 4, 3: 6, 4: 8, 5: 10}, 'Hello World', (1, 2, 3, 4, 5), [1, 2, 3, 4, 5])
        >>> dumps(deepcopy(({1: 1, 2: 4, 3: 6, 4: 8, 5: 10}, 'Hello World', (1, 2, 3, 4, 5), [1, 2, 3, 4, 5])))
        "((dp1\nI1\nI1\nsI2\nI4\nsI3\nI6\nsI4\nI8\nsI5\nI10\nsS'Hello World'\np2\n(I1\nI2\nI3\nI4\nI5\ntp3\n(lp4\nI1\naI2\naI3\naI4\naI5\nat."
        >>> dumps(deepcopy(t))
        "((dp1\nI1\nI1\nsI2\nI4\nsI3\nI6\nsI4\nI8\nsI5\nI10\nsS'Hello World'\np2\n(I1\nI2\nI3\nI4\nI5\ntp3\n(lp4\nI1\naI2\naI3\naI4\naI5\nat."
        >>> # Using deepcopy() beforehand means that now both dumps() are idential.
        >>> # It may not be necessary, but deepcopy() ensures that lookups will always work.

        Unfortunately calling copy() alone doesn't seem to fix the
        problem as it lies primarily with complex data types.

        >>> from cPickle import dumps
        >>> from copy import copy
        >>> t = ({1: 1, 2: 4, 3: 6, 4: 8, 5: 10}, 'Hello World', (1, 2, 3, 4, 5), [1, 2, 3, 4, 5])
        >>> dumps(copy(({1: 1, 2: 4, 3: 6, 4: 8, 5: 10}, 'Hello World', (1, 2, 3, 4, 5), [1, 2, 3, 4, 5])))
        "((dp1\nI1\nI1\nsI2\nI4\nsI3\nI6\nsI4\nI8\nsI5\nI10\nsS'Hello World'\np2\n(I1\nI2\nI3\nI4\nI5\ntp3\n(lp4\nI1\naI2\naI3\naI4\naI5\nat."
        >>> dumps(copy(t))
        "((dp1\nI1\nI1\nsI2\nI4\nsI3\nI6\nsI4\nI8\nsI5\nI10\nsS'Hello World'\n(I1\nI2\nI3\nI4\nI5\nt(lp2\nI1\naI2\naI3\naI4\naI5\natp3\n."

        """
        for value in self.testing_data:
            model_test = TestingModel(pickle_field=value, compressed_pickle_field=value)
            model_test.save()
            # Make sure that we can do an ``exact`` lookup by both the
            # pickle_field and the compressed_pickle_field.
            wrapped_value = wrap_conflictual_object(value)
            model_test = TestingModel.objects.get(pickle_field__exact=wrapped_value,
                                                  compressed_pickle_field__exact=wrapped_value)
            self.assertEquals(value, model_test.pickle_field)
            self.assertEquals(value, model_test.compressed_pickle_field)
            # Make sure that ``in`` lookups also work correctly.
            model_test = TestingModel.objects.get(pickle_field__in=[wrapped_value],
                                                  compressed_pickle_field__in=[wrapped_value])
            self.assertEquals(value, model_test.pickle_field)
            self.assertEquals(value, model_test.compressed_pickle_field)
            # Make sure that ``is_null`` lookups are working.
            self.assertEquals(1, TestingModel.objects.filter(pickle_field__isnull=False).count())
            self.assertEquals(0, TestingModel.objects.filter(pickle_field__isnull=True).count())
            model_test.delete()

        # Make sure that lookups of the same value work, even when referenced
        # differently. See the above docstring for more info on the issue.
        value = (D1, S1, T1, L1)
        model_test = TestingModel(pickle_field=value, compressed_pickle_field=value)
        model_test.save()
        # Test lookup using an assigned variable.
        model_test = TestingModel.objects.get(pickle_field__exact=value)
        self.assertEquals(value, model_test.pickle_field)
        # Test lookup using direct input of a matching value.
        model_test = TestingModel.objects.get(
            pickle_field__exact = (D1, S1, T1, L1),
            compressed_pickle_field__exact = (D1, S1, T1, L1),
        )
        self.assertEquals(value, model_test.pickle_field)
        model_test.delete()

    def testSerialization(self):
        model = MinimalTestingModel(pickle_field={'foo': 'bar'})
        serialized = serializers.serialize('json', [model])
        data = json.loads(serialized)

        # determine output at runtime, because pickle output in python 3
        # is different (but compatible with python 2)
        p = dbsafe_encode({'foo': 'bar'})

        self.assertEquals(data,
            [{'pk': None, 'model': 'picklefield.minimaltestingmodel',
              'fields': {"pickle_field": p}}])

        for deserialized_test in serializers.deserialize('json', serialized):
            self.assertEquals(deserialized_test.object,
                              model)
