from rest_framework.renderers import TemplateHTMLRenderer

from .store import ref_from_request


class ExtendedTemplateHTMLRenderer(TemplateHTMLRenderer):
    template_name = 'search/results.html'

    def resolve_context(self, data, request, response):
        """
        Adds some more data to the template context.
        """
        data['search_ref'] = ref_from_request(request)
        return super(ExtendedTemplateHTMLRenderer,
                     self).resolve_context(data, request, response)
