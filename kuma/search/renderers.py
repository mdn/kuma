from rest_framework.renderers import TemplateHTMLRenderer

from .filters import get_filters
from .models import Index
from .store import ref_from_request


class ExtendedTemplateHTMLRenderer(TemplateHTMLRenderer):
    template_name = 'search/results.html'
    exception_template_names = ['search/down.html']

    def resolve_context(self, data, request, response):
        """
        Adds some more data to the template context.
        """
        data['selected_filters'] = get_filters(request.query_params.getlist)
        data['search_ref'] = ref_from_request(request)
        data['index'] = Index.objects.get_current()
        return super(ExtendedTemplateHTMLRenderer,
                     self).resolve_context(data, request, response)

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Renders data to HTML, using Django's standard template rendering.

        The template name is determined by (in order of preference):

        1. An explicit .template_name set on the response.
        2. An explicit .template_name set on this class.
        3. The return result of calling view.get_template_names().

        FIXME: This is a copy of the render method from upstream to support
        passing the request to the render method of the template backend.
        This should be removed/fixed when moving to DRF 3.x.
        """
        renderer_context = renderer_context or {}
        view = renderer_context['view']
        request = renderer_context['request']
        response = renderer_context['response']

        if response.exception:
            template = self.get_exception_template(response)
        else:
            template_names = self.get_template_names(response, view)
            template = self.resolve_template(template_names)

        context = self.resolve_context(data, request, response)
        return template.render(context, request=request)
