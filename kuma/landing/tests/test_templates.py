from constance.test import override_config
from pyquery import PyQuery as pq

from kuma.core.tests import KumaTestCase
from kuma.core.urlresolvers import reverse
from kuma.search.models import Filter, FilterGroup


class HomeTests(KumaTestCase):
    def test_google_analytics(self):
        url = reverse('home')

        with override_config(GOOGLE_ANALYTICS_ACCOUNT='0'):
            response = self.client.get(url, follow=True)
            assert 200 == response.status_code
            assert 'ga(\'create' not in response.content

        with override_config(GOOGLE_ANALYTICS_ACCOUNT='UA-99999999-9'):
            response = self.client.get(url, follow=True)
            assert 200 == response.status_code
            assert 'ga(\'create' in response.content

    def test_default_search_filters(self):
        url = reverse('home')
        group = FilterGroup.objects.create(name='Topic', slug='topic')
        for name in ['CSS', 'HTML', 'JavaScript']:
            Filter.objects.create(group=group, name=name, slug=name.lower(),
                                  default=True)

        response = self.client.get(url, follow=True)
        page = pq(response.content)
        filters = page.find('#home-search-form input[type=hidden]')
        filter_vals = [p.val() for p in filters.items()]
        assert 'topic' == filters.eq(0).attr('name')
        assert {'css', 'html', 'javascript'} == set(filter_vals)
