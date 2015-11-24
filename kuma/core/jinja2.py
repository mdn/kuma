from __future__ import absolute_import

from jinja2 import Environment
from django_jinja.base import Template


class KumaEnvironment(Environment):

    def __init__(self, *args, **kwargs):
        super(KumaEnvironment, self).__init__(*args, **kwargs)
        self.template_class = Template
