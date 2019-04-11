# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .models import Banner


def get_banners(request):
    """
    Get all active banners ordered by priority
    """
    return {
        'banners': list(Banner.objects.filter(active=True).order_by('priority')),
    }
