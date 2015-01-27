from nose.plugins.attrib import attr
from nose.tools import eq_, ok_

from kuma.users.tests import UserTestCase
from kuma.core.urlresolvers import reverse

from pyquery import PyQuery as pq
from waffle.models import Switch


class RevisionsDashTest(UserTestCase):
    fixtures = UserTestCase.fixtures + ['wiki/documents.json']

    @attr('dashboards')
    def test_main_view(self):
        response = self.client.get(reverse('dashboards.revisions',
                                           locale='en-US'))
        eq_(200, response.status_code)
        ok_('text/html' in response['Content-Type'])
        ok_('dashboards/revisions.html' in
            [template.name for template in response.templates])

    @attr('dashboards')
    def test_revision_list(self):
        url = reverse('dashboards.revisions',
                      locale='en-US')
        # We only get revisions when requesting via AJAX.
        response = self.client.get(url,
                                   HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        eq_(200, response.status_code)

        page = pq(response.content)
        revisions = page.find('.dashboard-row')

        eq_(10, revisions.length)

        # Most recent revision first.
        eq_(29, int(pq(revisions[0]).attr('data-revision-id')))
        # Second-most-recent revision next.
        eq_(28, int(pq(revisions[1]).attr('data-revision-id')))
        # Oldest revision last.
        eq_(19, int(pq(revisions[-1]).attr('data-revision-id')))

    @attr('dashboards')
    def test_ip_link_on_switch(self):
        url = reverse('dashboards.revisions', locale='en-US')
        response = self.client.get(url)
        eq_(200, response.status_code)

        page = pq(response.content)
        ip_button = page.find('button#show_ips_btn')
        eq_([], ip_button)

        Switch.objects.create(name='store_revision_ips', active=True).save()
        self.client.login(username='admin', password='testpass')
        url = reverse('dashboards.revisions', locale='en-US')
        response = self.client.get(url)
        eq_(200, response.status_code)

        page = pq(response.content)
        ip_button = page.find('button#show_ips_btn')
        ok_(len(ip_button) > 0)

    @attr('dashboards')
    def test_locale_filter(self):
        url = reverse('dashboards.revisions', locale='fr') + '?locale=fr'
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        eq_(200, response.status_code)

        page = pq(response.content)
        revisions = page.find('.dashboard-row')

        ok_(len(revisions))
        eq_(1, revisions.length)

        ok_('fr' in pq(revisions[0]).find('.locale').html())

    @attr('dashboards')
    def test_user_lookup(self):
        url = reverse('dashboards.user_lookup',
                      locale='en-US') + '?user=test'
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        eq_(200, response.status_code)

        page = pq(response.content)
        revisions = page.find('.dashboard-row')

        for revision in revisions:
            author = pq(revision).find('.dashboard-author').text()
            ok_('test' in author)
            ok_('admin' not in author)

    @attr('dashboards')
    def test_creator_filter(self):
        url = reverse('dashboards.revisions',
                      locale='en-US') + '?user=testuser01'
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        eq_(200, response.status_code)

        page = pq(response.content)
        revisions = page.find('.dashboard-row')

        eq_(2, revisions.length)

        for revision in revisions:
            author = pq(revision).find('.dashboard-author').text()
            ok_('testuser01' in author)
            ok_('testuser2' not in author)

    @attr('dashboards')
    def test_topic_lookup(self):
        url = reverse('dashboards.topic_lookup',
                      locale='en-US') + '?topic=lorem'
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        eq_(200, response.status_code)

        page = pq(response.content)
        revisions = page.find('.dashboard-row')

        for revision in revisions:
            slug = pq(revision).find('.dashboard-title').html()
            ok_('lorem' in slug)
            ok_('article' not in slug)

    @attr('dashboards')
    def test_topic_filter(self):
        url = reverse('dashboards.revisions',
                      locale='en-US') + '?topic=article-with-revisions'
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        eq_(200, response.status_code)

        page = pq(response.content)
        revisions = page.find('.dashboard-row')

        eq_(6, revisions.length)
        for revision in revisions:
            ok_('lorem' not in pq(revision).find('.dashboard-title').html())
