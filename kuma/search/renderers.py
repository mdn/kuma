from rest_framework.renderers import TemplateHTMLRenderer

from .filters import get_filters
from .models import Index
from .store import ref_from_request


class ExtendedTemplateHTMLRenderer(TemplateHTMLRenderer):
    template_name = "search/results.html"
    exception_template_names = ["search/down.html"]

    def get_template_context(self, data, renderer_context):
        request = renderer_context["request"]
        new_data = {
            "selected_filters": get_filters(request.query_params.getlist),
            "search_ref": ref_from_request(request),
            "index": Index.objects.get_current(),
        }

        data.update(new_data)

        return super(ExtendedTemplateHTMLRenderer, self).get_template_context(
            data, renderer_context
        )
