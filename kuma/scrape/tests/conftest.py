# -*- coding: utf-8 -*-
"""py.test fixtures"""
from __future__ import unicode_literals
from datetime import datetime

import pytest


@pytest.fixture
def simple_user(db, django_user_model):
    """A simple User record with only the basic information."""
    return django_user_model.objects.create(
        username='JackDeveloper',
        email='jack@example.com',
        date_joined=datetime(2016, 11, 4, 9, 1))


@pytest.fixture
def simple_user_html(simple_user, client):
    """The profile HTML for a simple user."""
    response = client.get('/en-US/profiles/' + simple_user.username)
    return response.content
