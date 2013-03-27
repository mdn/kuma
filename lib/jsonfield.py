from django.db import models
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import simplejson as json


class JSONField(models.TextField):
    """JSONField is a generic textfield that neatly serializes/unserializes
    JSON objects seamlessly
    see: http://djangosnippets.org/snippets/1478/
    """

    # Used so to_python() is called
    __metaclass__ = models.SubfieldBase

    def to_python(self, value):
        """Convert our string value to JSON after we load it from the DB"""
        if not value:
            return dict()
        try:
            if (isinstance(value, basestring) or
                    type(value) is unicode):
                return json.loads(value)
        except ValueError:
            return dict()
        return value

    def get_db_prep_save(self, value, connection):
        """Convert our JSON object to a string before we save"""
        if not value:
            return '{}'
        if isinstance(value, dict):
            value = json.dumps(value, cls=DjangoJSONEncoder)
        return super(JSONField, self).get_db_prep_save(value, connection)


# Tell South that this field isn't all that special
try:
    import south.modelsinspector
    south.modelsinspector.add_introspection_rules([], ["^jsonfield.JSONField"])
except ImportError, e:
    pass
