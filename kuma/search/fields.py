from django.conf import settings

from rest_framework import serializers

from kuma.core.urlresolvers import reverse


class QueryParameterField(serializers.Field):
    param_name = None
    method = 'get'
    empty_value = None

    def to_native(self, value):
        request = self.context.get('request')
        getter = getattr(request.QUERY_PARAMS, self.method)
        return getter(self.param_name, self.empty_value)


class SearchQueryField(QueryParameterField):
    """
    Field that returns the search query of the current request.
    """
    param_name = 'q'


class LocaleField(serializers.Field):

    def to_native(self, value):
        request = self.context.get('request')
        return request.locale


class SiteURLField(serializers.Field):
    """
    A serializer field for creating URL for the given objects with the
    given ``args``/``kwargs`` and a required ``locale`` attribute.
    """
    def __init__(self, url_name, args=None, kwargs=None):
        self.url_name = url_name
        self.args = args or []
        self.kwargs = kwargs or {}
        super(SiteURLField, self).__init__(source='*')

    def to_native(self, value):
        if not value:
            return None
        args = [serializers.get_component(value, arg) for arg in self.args]
        kwargs = dict((arg, serializers.get_component(value, arg))
                      for arg in self.kwargs)
        locale = getattr(value, 'locale', settings.LANGUAGE_CODE)
        path = reverse(self.url_name, locale=locale, args=args, kwargs=kwargs)
        return '%s%s' % (settings.SITE_URL, path)
