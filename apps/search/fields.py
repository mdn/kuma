from rest_framework import serializers


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


class DocumentExcerptField(serializers.Field):
    """
    A serializer field that given a wiki DocumentType object returns
    a cleaned version of the excerpt fields with the highlighting
    <em> tag intact.
    """
    def to_native(self, value):
        if not value._highlight:
            return value.summary
        return value.get_excerpt()
