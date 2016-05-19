from django_jinja import library

from ..utils import allow_add_attachment_by


library.global_function(allow_add_attachment_by)
