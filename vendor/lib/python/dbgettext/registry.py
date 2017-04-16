from django.db.models.base import ModelBase

class Options(object):
    """
    Encapsulates dbgettext options for a given model 

    - attributes: 
        tuple of names of fields/callables to be translated
    - parsed_attributes: 
        dictionary of names of fields/callables with HTML content which should 
        have translatable content extracted (should not be listed in 
        attributes), with their associated lexicons
    - translate_if:
        dictionary used to filter() queryset 
    - get_path_identifier:
        function returning string used to identify object in path to exported 
        content (given an object)
    - parent:
        name of foreign key to parent model, if registered. Affects:
        - path (path_identifier appended onto parent path)
        - queryset (object only translated if parent is)
    - custom_lexicon_rules
        list of extra custom rules ((regexp, function) tuples) to be applied
        when parsing HTML -- see html.py

    """

    attributes = ()
    parsed_attributes = {}
    translate_if = {}
    parent = None
    
    def get_path_identifier(self, obj):
        return '%s_%s' % (obj._meta.object_name, str(obj.pk))


# Registration code based on django.contrib.admin.sites

class AlreadyRegistered(Exception):
    pass

class NotRegistered(Exception):
    pass

class Registry(object):
    """
    A Registry object is used to register() models for dbgettext exporting,
    together with their associated options.
    """

    def __init__(self):
        self._registry = {} # model_class class -> Options subclass

    def register(self, model_or_iterable, options_class, **options):
        """
        Registers the given model(s) with the given admin class.

        The model(s) should be Model classes, not instances.

        If a model is already registered, this will raise AlreadyRegistered.
        """

        if isinstance(model_or_iterable, ModelBase):
            model_or_iterable = [model_or_iterable]
        for model in model_or_iterable:
            if model in self._registry:
                raise AlreadyRegistered(
                    'The model %s is already registered' % model.__name__)

            self._registry[model] = options_class() # instantiated

    def unregister(self, model_or_iterable):
        """
        Unregisters the given model(s).

        If a model isn't already registered, this will raise NotRegistered.
        """
        if isinstance(model_or_iterable, ModelBase):
            model_or_iterable = [model_or_iterable]
        for model in model_or_iterable:
            if model not in self._registry:
                raise NotRegistered(
                    'The model %s is not registered' % model.__name__)
            del self._registry[model]


# Global Registry object
registry = Registry()
