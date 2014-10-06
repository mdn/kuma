from django.template.defaultfilters import slugify
from dbgettext.registry import registry, Options

from .models import Filter, FilterGroup


class FilterOptions(Options):
    attributes = ('name',)

    def get_path_identifier(self, obj):
        return obj.slug


class FilterGroupOptions(Options):
    attributes = ('name',)

    def get_path_identifier(self, obj):
        return slugify(obj.name)


registry.register(Filter, FilterOptions)
registry.register(FilterGroup, FilterGroupOptions)
