# -*- coding: utf-8 -*-
"""Tests for the LinksSource class (Links from a page)."""
from __future__ import unicode_literals

from datetime import datetime

from django.conf import settings

from kuma.wiki.models import Revision

from . import mock_requester, mock_storage
from ..sources import LinksSource


def test_init_blank():
    source = LinksSource()
    assert source.path == '/en-US/'
    assert source.locale == 'en-US'


def test_init_slash():
    source = LinksSource('/')
    assert source.path == '/en-US/'


def test_init_full_url():
    url = 'https://wiki.developer.mozilla.org/en-US/docs/Web/CSS'
    source = LinksSource(url)
    assert source.path == '/en-US/docs/Web/CSS'
    assert source.locale == 'en-US'


def test_init_non_english():
    url = '/fr/docs/Web/CSS'
    source = LinksSource(url)
    assert source.path == '/fr/docs/Web/CSS'
    assert source.locale == 'fr'


def test_gather_homepage(client, db):
    source = LinksSource('/')
    html = client.get('/en-US/', HTTP_HOST=settings.WIKI_HOST).content
    requester = mock_requester(content=html)
    storage = mock_storage()
    resources = source.gather(requester, storage)
    assert source.state == source.STATE_DONE
    assert source.freshness == source.FRESH_YES

    # The exact list of resources will change as the homepage changes
    expected_paths = [
        '/en-US/docs/Learn',
        '/en-US/docs/Tools',
        '/en-US/docs/Web/JavaScript',
    ]
    for path in expected_paths:
        spec = ('document', path, {})
        assert spec in resources

    # These appear on the homepage, but shouldn't be in the paths to scrape
    unexpected_paths = [
        '/en-US/search',
    ]
    for path in unexpected_paths:
        spec = ('document', path, {})
        assert spec not in resources


def test_gather_ignores_links(client, root_doc, simple_user):
    user_profile_url = simple_user.get_absolute_url()
    content = """
<ul>
  <li><a href="/en-US/docs/Absolute/Link">Absolute Link</a></li>
  <li><a href="Relative/Link">Relative Link</a></li>
  <li><a href="#later">Later in this page.</a></li>
  <li><a href="%s">Profile Link</a></li>
</ul>
""" % user_profile_url
    new_rev = Revision(
        document=root_doc,
        creator=root_doc.current_revision.creator,
        content=content,
        created=datetime(2017, 6, 5))
    new_rev.save()
    base_path = root_doc.get_absolute_url()
    html = client.get(base_path, HTTP_HOST=settings.WIKI_HOST).content

    source = LinksSource(base_path)
    requester = mock_requester(content=html)
    storage = mock_storage()
    resources = source.gather(requester, storage)
    assert source.state == source.STATE_DONE
    assert source.freshness == source.FRESH_YES

    expected = ('document', '/en-US/docs/Absolute/Link', {})
    assert expected in resources

    for doc, path, options in resources:
        assert base_path not in path
        assert "Relative/Link" not in path
        assert "#later" not in path
        assert user_profile_url not in path
