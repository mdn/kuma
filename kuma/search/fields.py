from django.conf import settings
from rest_framework import serializers

from kuma.core.urlresolvers import reverse


class SearchQueryField(serializers.ReadOnlyField):
    """
    Field that returns the search query of the current request.
    """

    def __init__(self, *args, **kwargs):
        kwargs["source"] = "*"
        super(SearchQueryField, self).__init__(*args, **kwargs)

    def to_representation(self, value):
        request = self.context.get("request")
        if request is None:
            return ""
        else:
            return request.query_params.get("q", None)


class SiteURLField(serializers.ReadOnlyField):
    """
    A serializer field for creating URL for the given objects with the
    given ``args``/``kwargs`` and a required ``locale`` attribute.
    """

    def __init__(self, url_name, args=None, kwargs=None):
        self.url_name = url_name
        self.args = args or []
        self.kwargs = kwargs or []
        super(SiteURLField, self).__init__(source="*")

    def to_representation(self, value):
        if not value:
            return None
        args = [getattr(value, arg) for arg in self.args]
        kwargs = {arg: getattr(value, arg) for arg in self.kwargs}
        locale = getattr(value, "locale", settings.LANGUAGE_CODE)
        return reverse(self.url_name, locale=locale, args=args, kwargs=kwargs)
