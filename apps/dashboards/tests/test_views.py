import json

from nose.plugins.attrib import attr
from nose.tools import eq_, ok_

from waffle.models import Flag

from sumo.tests import TestCase
from sumo.urlresolvers import reverse


class RevisionsDashTest(TestCase):
    fixtures = ['test_users.json', 'wiki/documents.json']

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

        revision_json = json.loads(response.content)
        eq_(10, revision_json['iTotalRecords'])

        revisions = revision_json['aaData']
        eq_(10, len(revisions))
        # Most recent revision first.
        eq_(29, revisions[0]['id'])
        # Second-most-recent revision next.
        eq_(28, revisions[1]['id'])
        # Oldest revision last.
        eq_(19, revisions[-1]['id'])
        

    @attr('dashboards')
    def test_locale_filter(self):
        url = reverse('dashboards.revisions', locale='fr') + '?locale=fr'
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        eq_(200, response.status_code)
        revisions = json.loads(response.content)
        ok_(len(revisions))
        eq_(1, revisions['iTotalRecords'])
        eq_(1, len(revisions['aaData']))
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
                      locale='en-US') + '?user=testuser01'
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        eq_(200, response.status_code)
        revisions = json.loads(response.content)
        ok_(len(revisions))
        eq_(2, revisions['iTotalRecords'])
        ok_(['testuser01' == rev['creator'] for rev in revisions['aaData']])
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
                      locale='en-US') + '?topic=article-with-revisions'
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        eq_(200, response.status_code)
        revisions = json.loads(response.content)
        ok_(len(revisions))
        eq_(6, revisions['iTotalRecords'])
        eq_(6, len(revisions['aaData']))
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
