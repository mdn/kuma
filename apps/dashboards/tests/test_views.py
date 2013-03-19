import json

from nose.plugins.attrib import attr
from nose.tools import eq_, ok_
from pyquery import PyQuery as pq

from waffle.models import Flag

from dashboards.readouts import CONTRIBUTOR_READOUTS
from sumo.tests import TestCase
from sumo.urlresolvers import reverse

class LocalizationDashTests(TestCase):
    def test_redirect_to_contributor_dash(self):
        """Should redirect to Contributor Dash if the locale is the default"""
        response = self.client.get(reverse('dashboards.localization',
                                           locale='en-US'),
                                   follow=True)
        self.assertRedirects(response, reverse('dashboards.contributors',
                                               locale='en-US'))


class ContributorDashTests(TestCase):
    def test_main_view(self):
        """Assert the top page of the contributor dash resolves, renders."""
        response = self.client.get(reverse('dashboards.contributors',
                                           locale='en-US'))
        eq_(200, response.status_code)

    def test_detail_view(self):
        """Assert the detail page of the contributor dash resolves, renders."""
        response = self.client.get(reverse('dashboards.contributors_detail',
            args=[CONTRIBUTOR_READOUTS[CONTRIBUTOR_READOUTS.keys()[0]].slug],
            locale='en-US'))
        eq_(200, response.status_code)


class RevisionsDashTest(TestCase):
    fixtures = ['test_users.json', 'wiki/documents.json']

    def setUp(self):
        super(RevisionsDashTest, self).setUp()
        self.dashboard_flag = Flag.objects.create(name='revisions_dashboard',
                                                  everyone=True)

    @attr('dashboards')
    def test_main_view(self):
        response = self.client.get(reverse('dashboards.revisions',
                                           locale='en-US'))
        eq_(200, response.status_code)
        ok_('text/html' in response['Content-Type'])
        ok_('dashboards/revisions.html' in
            [template.name for template in response.template])

    @attr('dashboards')
    def test_locale_filter(self):
        url = reverse('dashboards.revisions', locale='fr')
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        eq_(200, response.status_code)
        revisions = json.loads(response.content)
        ok_(['fr' in rev['doc_url'] for rev in revisions['aaData']])
        ok_(['en-US' not in rev['doc_url'] for rev in revisions['aaData']])

    @attr('dashboards')
    def test_user_lookup(self):
        url = reverse('dashboards.user_lookup',
                      locale='en-US') + '?user=test'
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        eq_(200, response.status_code)
        users = json.loads(response.content)
        ok_(['test' in user['label'] for user in users])
        ok_(['admin' not in user['label'] for user in users])

    @attr('dashboards')
    def test_creator_filter(self):
        url = reverse('dashboards.revisions',
                      locale='en-US') + '?user=testuser'
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        eq_(200, response.status_code)
        revisions = json.loads(response.content)
        ok_(['testuser' == rev['creator'] for rev in revisions['aaData']])
        ok_(['testuser2' != rev['creator'] for rev in revisions['aaData']])

    @attr('dashboards')
    def test_topic_lookup(self):
        url = reverse('dashboards.topic_lookup',
                      locale='en-US') + '?topic=lorem'
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        eq_(200, response.status_code)
        slugs = json.loads(response.content)
        ok_(['lorem' in slug['label'] for slug in slugs])
        ok_(['article' not in slug['label'] for slug in slugs])

    @attr('dashboards')
    def test_topic_filter(self):
        url = reverse('dashboards.revisions',
                      locale='en-US') + '?topic=article'
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        eq_(200, response.status_code)
        revisions = json.loads(response.content)
        ok_(['lorem' not in rev['slug'] for rev in revisions['aaData']])

    @attr('dashboards')
    def test_newuser_filter_waffle(self):
        url = reverse('dashboards.revisions', locale='en-US')
        response = self.client.get(url)
        eq_(200, response.status_code)
        ok_('revision-dashboard-newusers' not in response.content)

        rev_dash_newusers = Flag.objects.create(
            name='revision-dashboard-newusers', everyone=True)
        rev_dash_newusers.save()

        url = reverse('dashboards.revisions', locale='en-US')
        response = self.client.get(url)
        eq_(200, response.status_code)
        ok_('revision-dashboard-newusers' in response.content)
