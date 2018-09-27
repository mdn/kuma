from __future__ import unicode_literals

import mock

from pyquery import PyQuery as pq

from kuma.core.urlresolvers import reverse
from kuma.search.models import Filter, FilterGroup


def test_google_analytics_disabled(constance_config, client):
    constance_config.GOOGLE_ANALYTICS_ACCOUNT = '0'
    response = client.get(reverse('home'), follow=True)
    assert 200 == response.status_code
    assert b"ga('create" not in response.content


def test_google_analytics_enabled(constance_config, client):
    constance_config.GOOGLE_ANALYTICS_ACCOUNT = 'UA-99999999-9'
    response = client.get(reverse('home'), follow=True)
    assert 200 == response.status_code
    assert b"ga('create" in response.content


def test_default_search_filters(db, client):
    group = FilterGroup.objects.create(name='Topic', slug='topic')
    for name in ['CSS', 'HTML', 'JavaScript']:
        Filter.objects.create(group=group, name=name, slug=name.lower(),
                              default=True)

    response = client.get(reverse('home'), follow=True)
    page = pq(response.content)
    filters = page.find('#home-search-form input[type=hidden]')

    assert 'topic' == filters.eq(0).attr('name')
    assert set(p.val() for p in filters.items()) == {'css', 'html', 'javascript'}


@mock.patch('kuma.contributions.context_processors.enabled')
def test_does_not_include_csrf(mock_enabled, db, user_client):
    """
    The document should not include CSRF tokens, since it causes
    problems when used with a CDN like CloudFront (see bugzilla #1456165).
    """
    mock_enabled.return_value = True
    resp = user_client.get(reverse('home'))
    doc = pq(resp.content)
    assert not doc('input[name="csrfmiddlewaretoken"]')
