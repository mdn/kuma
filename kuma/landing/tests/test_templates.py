from __future__ import unicode_literals

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
