import django
from django.db import models
from django.utils import six

# python 3.x does not have cPickle module
try:
    # cpython 2.x
    from cPickle import loads, dumps  # noqa
except ImportError:
    from pickle import loads, dumps  # noqa

if django.VERSION >= (1, 8):
    _PickledObjectField = models.Field
else:
    _PickledObjectField = six.with_metaclass(models.SubfieldBase, models.Field)
