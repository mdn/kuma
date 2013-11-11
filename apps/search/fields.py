from rest_framework import serializers


class SearchQueryField(serializers.Field):
    """
    Field that returns a link to the next page in paginated results.
    """
    search_param = 'q'

    def to_native(self, value):
        request = self.context.get('request')
        return request.QUERY_PARAMS.get(self.search_param, None)


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
