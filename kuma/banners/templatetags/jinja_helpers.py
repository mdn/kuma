# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django_jinja import library

from ..models import Banner


@library.global_function
def get_banners():
    """
    Get all active banners ordered by priority
    """
    return list(Banner.objects.filter(active=True).order_by('priority'))
