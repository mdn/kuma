from django.core.management.base import BaseCommand
from django.template import engines

from kuma.search.models import FilterGroup

TEMPLATE = """\
'''
Names of filters and filter groups in the search interface.

This is generated from the production database using the management command:

./manage.py generate_search_names.py
'''
from django.utils.translation import gettext_lazy as _

FILTER_NAMES = {
  {%- for group_name, filter_names in names %}
    _('{{ group_name | replace("'", "\\\\'") | safe }}'): [
      {%- for filter_name in filter_names %}
        _('{{ filter_name | replace("'", "\\\\'") | safe }}'){% if not loop.last %},{% endif %}
      {%- endfor %}
    ]{% if not loop.last %},{% endif %}
  {%- endfor %}
}
"""


class Command(BaseCommand):
    help = "Generates search UI names for kuma/search/names.py"

    def handle(self, *args, **options):
        names = []
        for group in FilterGroup.objects.order_by("name"):
            filter_names = group.filters.values_list("name", flat=True)
            names.append((group.name, sorted(filter_names)))

        engine = engines["jinja2"]
        template = engine.from_string(TEMPLATE)
        out = template.render({"names": names})
        self.stdout.write(out)
