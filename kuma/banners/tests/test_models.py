# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest

from ..models import Banner


@pytest.mark.django_db
def test_add_new_banner():
    """Test that banner creation succeeds"""
    sample_banner = {
        "name": "GreatSuccess",
        "title": "Active Banner",
        "main_copy": "Some sample main copy",
        "button_copy": "Click Me!",
        "theme": "default",
        "active": True,
        "priority": "2"
    }
    banner = Banner.objects.create(**sample_banner)

    assert banner.name == "GreatSuccess"


@pytest.mark.django_db
def test_default_theme_set():
    """Test that theme is set to default if empty"""
    sample_banner = {
        "name": "notheme",
        "title": "Inactive Banner",
        "main_copy": "Some sample main copy",
        "button_copy": "Click Me!",
        "active": False,
        "priority": "1"
    }
    banner = Banner.objects.create(**sample_banner)

    assert banner.theme == "default"


@pytest.mark.django_db
def test_default_priority_set():
    """Test that priority is set to 100 if empty"""
    sample_banner = {
        "name": "nopriority",
        "title": "Inactive Banner",
        "main_copy": "Some sample main copy",
        "button_copy": "Click Me!",
        "theme": "default",
        "active": False
    }
    banner = Banner.objects.create(**sample_banner)

    assert banner.priority == 100


@pytest.mark.django_db
def test_activate_banner():
    """Test changing banner state from inactive to active"""
    sample_banner = {
        "name": "inactive",
        "title": "Inactive Banner",
        "main_copy": "Some sample main copy",
        "button_copy": "Click Me!",
        "theme": "default",
        "active": False,
        "priority": "1"
    }
    banner = Banner.objects.create(**sample_banner)
    assert banner.active is False

    banner.active = True
    banner.save()

    banner2 = Banner.objects.get(pk=banner.pk)
    assert banner2.active
