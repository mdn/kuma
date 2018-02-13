from dbgettext.registry import registry, Options
from django.apps import AppConfig
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _


class FilterOptions(Options):
    """Options for extracting Filter names with dbgettext."""
    attributes = ('name',)

    def get_path_identifier(self, obj):
        return obj.slug


class FilterGroupOptions(Options):
    """Options for extracting FilterGroup names with dbgettext."""
    attributes = ('name',)

    def get_path_identifier(self, obj):
        return slugify(obj.name)


class SearchConfig(AppConfig):
    """Django config for the kuma.search app."""
    name = 'kuma.search'
    verbose_name = _('Search')

    def ready(self):
        super(SearchConfig, self).ready()

        registry.register(self.get_model('Filter'), FilterOptions)
        registry.register(self.get_model('FilterGroup'), FilterGroupOptions)
