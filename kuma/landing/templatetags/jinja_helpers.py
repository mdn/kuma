from django_jinja import library

from ..utils import favicon_url

library.global_function(favicon_url)
