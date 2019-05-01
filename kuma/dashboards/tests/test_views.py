# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime
import json

import mock
import pytest
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import override
from pyquery import PyQuery as pq
from waffle.testutils import override_switch

from kuma.core.tests import (assert_no_cache_header,
                             assert_shared_cache_header)
from kuma.core.urlresolvers import reverse
from kuma.core.utils import to_html, urlparams
from kuma.dashboards.forms import RevisionDashboardForm
from kuma.users.tests import create_document, SampleRevisionsMixin, UserTestCase
from kuma.wiki.models import (Document, DocumentSpamAttempt, Revision,
                              RevisionAkismetSubmission)


REVS_PER_USER = 3  # Number of revisions per user in dashboard_revisions


@pytest.fixture
def dashboard_revisions(wiki_user, wiki_user_2, wiki_user_3):
    """Revisions, in reverse creation order, for testing the dashboard."""

    revisions = []
    day = datetime.datetime(2018, 4, 1)
    users = wiki_user, wiki_user_2, wiki_user_3
    languages = {
        'de': ("%s's Dokument", '<p>Zweiter Schnitt von %s</p>'),
        'es': ('El Documento de %s', '<p>Segunda edición por %s</p>'),
        'fr': ('Le Document de %s', '<p>Deuxième édition par %s</p>'),
    }
    for user, lang in zip(users, sorted(languages.keys())):
        en_title = user.username + ' Document'
        en_doc = Document.objects.create(
            locale='en-US', slug=user.username + '-doc', title=en_title)
        first_rev = Revision.objects.create(
            document=en_doc, creator=user, title=en_title,
            content='<p>First edit by %s</p>' % user.username,
            created=day)
        trans_title, trans_content = (
            fmt % user.username for fmt in languages[lang])
        trans_doc = Document.objects.create(
            locale=lang, slug=user.username + '-doc', title=trans_title)
        trans_rev = Revision.objects.create(
            document=trans_doc, creator=user, title=trans_title,
            content=trans_content,
            created=day + datetime.timedelta(seconds=2 * 60 * 60))
        third_rev = Revision.objects.create(
            document=en_doc, creator=user, title=en_title,
            content='<p>Third edit by %s</p>' % user.username,
            created=day + datetime.timedelta(seconds=3 * 60 * 60))
        revisions.extend((first_rev, trans_rev, third_rev))
        day += datetime.timedelta(days=1)

    revisions.reverse()
    return revisions


@pytest.fixture
def known_author(wiki_user):
    """Add wiki_user to the Known Users group."""
    group = Group.objects.create(name='Known Authors')
    group.user_set.add(wiki_user)
    return wiki_user


def test_revisions_not_logged_in(root_doc, client):
    """A user who is not logged in can't see the revisions dashboard."""
    url = reverse('dashboards.revisions')
    response = client.get(url)
    assert response.status_code == 302
    assert response['Location'] == '/en-US/users/signin?next={}'.format(url)
    assert_no_cache_header(response)


def test_revisions(root_doc, user_client):
    """The revision dashboard works for logged in users."""
    response = user_client.get(reverse('dashboards.revisions'))
    assert response.status_code == 200
    assert 'Cache-Control' in response
    assert_no_cache_header(response)
    assert 'text/html' in response['Content-Type']
    assert ('dashboards/revisions.html' in
            (template.name for template in response.templates))


def test_revisions_list_via_AJAX(dashboard_revisions, user_client):
    """The full list of revisions can be returned via AJAX."""
    response = user_client.get(reverse('dashboards.revisions'),
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert response.status_code == 200
    page = pq(response.content)
    rev_rows = page.find('.dashboard-row')
    assert rev_rows.length == len(dashboard_revisions) == 3 * REVS_PER_USER

    # Revisions are in order, most recent first
    for rev_row, revision in zip(rev_rows, dashboard_revisions):
        assert int(rev_row.attrib['data-revision-id']) == revision.id


@pytest.mark.parametrize('switch', (True, False))
@pytest.mark.parametrize('is_admin', (True, False))
def test_revisions_show_ips_button(switch, is_admin, root_doc, user_client,
                                   admin_client):
    """Toggle IPs button appears for admins when the switch is active."""
    client = admin_client if is_admin else user_client
    with override_switch('store_revision_ips', active=switch):
        response = client.get(reverse('dashboards.revisions'))
    assert response.status_code == 200
    page = pq(response.content)
    ip_button = page.find('button#show_ips_btn')
    assert len(ip_button) == (1 if (switch and is_admin) else 0)


@pytest.mark.parametrize('has_perm', (True, False))
def test_revisions_show_spam_submission_button(has_perm, root_doc, wiki_user,
                                               user_client):
    """Submit as spam button appears when the user has the permission."""
    if has_perm:
        content_type = ContentType.objects.get_for_model(
            RevisionAkismetSubmission)
        perm = Permission.objects.get(
            codename='add_revisionakismetsubmission',
            content_type=content_type)
        wiki_user.user_permissions.add(perm)

    response = user_client.get(reverse('dashboards.revisions'))
    assert response.status_code == 200
    page = pq(response.content)
    spam_report_button = page.find('.spam-ham-button')
    assert len(spam_report_button) == (1 if has_perm else 0)


def test_revisions_locale_filter(dashboard_revisions, user_client):
    """Revisions can be filtered by locale."""
    url = urlparams(reverse('dashboards.revisions', locale='fr'),
                    locale='fr')
    response = user_client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert response.status_code == 200

    page = pq(response.content)
    revisions = page.find('.dashboard-row')
    assert revisions.length == 1
    locale = to_html(revisions.find('.locale'))
    assert locale == 'fr'


def test_revisions_creator_filter(dashboard_revisions, user_client):
    """Revisions can be filtered by a username."""
    url = urlparams(reverse('dashboards.revisions'), user='wiki_user_2')
    response = user_client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert response.status_code == 200

    page = pq(response.content)
    revisions = page.find('.dashboard-row')
    assert revisions.length == REVS_PER_USER
    authors = revisions.find('.dashboard-author')
    assert authors.length == REVS_PER_USER
    for author in authors:
        assert author.text_content().strip() == 'wiki_user_2'


def test_revisions_topic_filter(dashboard_revisions, user_client):
    """Revisions can be filtered by topic (the document slug)."""
    url = urlparams(reverse('dashboards.revisions'), topic='wiki_user_2-doc')
    response = user_client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert response.status_code == 200

    page = pq(response.content)
    revisions = page.find('.dashboard-row')
    assert revisions.length == REVS_PER_USER
    slugs = revisions.find('.dashboard-slug')
    assert slugs.length == REVS_PER_USER
    for slug in slugs:
        assert slug.text_content() == 'wiki_user_2-doc'


@pytest.mark.parametrize('authors', (RevisionDashboardForm.KNOWN_AUTHORS,
                                     RevisionDashboardForm.UNKNOWN_AUTHORS,
                                     RevisionDashboardForm.ALL_AUTHORS))
def test_revisions_known_authors_filter(authors, dashboard_revisions,
                                        user_client, known_author):
    """Revisions can be filtered by the Known Authors group."""
    url = urlparams(reverse('dashboards.revisions'), authors=authors)
    response = user_client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert response.status_code == 200

    page = pq(response.content)
    revisions = page.find('.dashboard-row')
    counts = {
        RevisionDashboardForm.KNOWN_AUTHORS: REVS_PER_USER,
        RevisionDashboardForm.UNKNOWN_AUTHORS: 2 * REVS_PER_USER,
        RevisionDashboardForm.ALL_AUTHORS: 3 * REVS_PER_USER}
    expected_count = counts[authors]
    assert revisions.length == expected_count
    author_spans = revisions.find('.dashboard-author')
    assert author_spans.length == expected_count
    if authors != RevisionDashboardForm.ALL_AUTHORS:
        for author_span in author_spans:
            username = author_span.text_content().strip()
            if authors == RevisionDashboardForm.KNOWN_AUTHORS:
                assert username == known_author.username
            else:
                assert username != known_author.username


def test_revisions_creator_overrides_known_authors_filter(
        dashboard_revisions, user_client, known_author):
    """If the creator filter is set, the Known Authors filter is ignored."""
    url = urlparams(reverse('dashboards.revisions'),
                    user='wiki_user_3',
                    authors=RevisionDashboardForm.KNOWN_AUTHORS)
    response = user_client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert response.status_code == 200
    page = pq(response.content)
    revisions = page.find('.dashboard-row')
    assert revisions.length == REVS_PER_USER
    author_spans = revisions.find('.dashboard-author')
    assert author_spans.length == REVS_PER_USER
    for author_span in author_spans:
        username = author_span.text_content().strip()
        assert username == 'wiki_user_3'


@mock.patch('kuma.dashboards.utils.analytics_upageviews')
class SpamDashTest(SampleRevisionsMixin, UserTestCase):
    fixtures = UserTestCase.fixtures + ['wiki/documents.json']

    def test_not_logged_in(self, mock_analytics_upageviews):
        """A user who is not logged in is not able to see the dashboard."""
        response = self.client.get(reverse('dashboards.spam'))
        assert response.status_code == 302
        assert_no_cache_header(response)

    def test_permissions(self, mock_analytics_upageviews):
        """A user with correct permissions is able to see the dashboard."""
        self.client.login(username='testuser', password='testpass')
        # Attempt to see spam dashboard as a logged-in user without permissions
        response = self.client.get(reverse('dashboards.spam'))
        assert response.status_code == 403

        # Give testuser wiki.add_revisionakismetsubmission permission
        perm_akismet = Permission.objects.get(codename='add_revisionakismetsubmission')
        self.testuser.user_permissions.add(perm_akismet)
        response = self.client.get(reverse('dashboards.spam'))
        assert response.status_code == 403

        # Give testuser wiki.add_documentspamattempt permission
        perm_spam = Permission.objects.get(codename='add_documentspamattempt')
        self.testuser.user_permissions.add(perm_spam)
        response = self.client.get(reverse('dashboards.spam'))
        assert response.status_code == 403

        # Give testuser wiki.add_userban permission
        perm_ban = Permission.objects.get(codename='add_userban')
        self.testuser.user_permissions.add(perm_ban)
        response = self.client.get(reverse('dashboards.spam'))
        # With all correct permissions testuser is able to see the dashboard
        assert response.status_code == 200
        assert_no_cache_header(response)
        assert 'text/html' in response['Content-Type']
        assert 'dashboards/spam.html' in (template.name for template in response.templates)

    def test_misconfigured_google_analytics_does_not_block(self, mock_analytics_upageviews):
        """If the constance setting for the Google Analytics API credentials is not
        configured, or is misconfigured, calls to analytics_upageviews will
        raise an ImproperlyConfigured error.  Show that we still get the rest of
        the stats, along with a message.

        """
        mock_analytics_upageviews.side_effect = ImproperlyConfigured("Oops!")

        rev = self.create_revisions(
            num=1,
            creator=self.testuser,
            document=self.document
        )[0]
        rev.created = datetime.datetime.today() - datetime.timedelta(days=1)
        rev.save()
        rev.akismet_submissions.create(sender=self.admin, type='spam')

        self.client.login(username='admin', password='testpass')
        # The first response will say that the report is being processed
        response = self.client.get(reverse('dashboards.spam'))
        assert 200 == response.status_code

        response2 = self.client.get(reverse('dashboards.spam'))

        self.assertContains(response2, "Oops!", status_code=200)
        page = pq(response2.content)
        spam_trends_table = page.find('.spam-trends-table')
        assert 1 == len(spam_trends_table)
        spam_events_table = page.find('.spam-events-table')
        assert 1 == len(spam_events_table)

    def test_recent_spam_revisions_show(self, mock_analytics_upageviews):
        """The correct spam revisions should show up."""
        doc1 = create_document(save=True)
        doc2 = create_document(save=True)
        # Create some revisions by self.testuser
        rev_doc0 = self.create_revisions(
            num=1,
            creator=self.testuser,
            document=self.document
        )
        rev_doc1 = self.create_revisions(num=1, creator=self.testuser, document=doc1)
        rev_doc2 = self.create_revisions(num=1, creator=self.testuser, document=doc2)
        created_revisions = rev_doc0 + rev_doc1 + rev_doc2
        # Mark each revision as created yesterday
        for rev in created_revisions:
            rev.created = datetime.datetime.today() - datetime.timedelta(days=1)
            rev.save()
        # Mark each of self.testuser's revisions as spam
        for revision in created_revisions:
            revision.akismet_submissions.create(sender=self.admin, type="spam")
        # self.admin creates some revisions on a different document
        self.create_revisions(num=3, creator=self.admin)

        mock_analytics_upageviews.return_value = {
            rev_doc0[0].id: 0,
            rev_doc1[0].id: 0,
            rev_doc2[0].id: 0
        }

        self.client.login(username='admin', password='testpass')
        # The first response will say that the report is being processed
        response = self.client.get(reverse('dashboards.spam'))
        assert 200 == response.status_code

        response2 = self.client.get(reverse('dashboards.spam'))
        page = pq(response2.content)
        table_rows = page.find('.spam-events-table tbody tr')
        table_row_text = ''
        for table_row in table_rows:
            table_row_text += table_row.text_content()

        assert len(table_rows) == len(created_revisions)
        for revision in created_revisions:
            document_url = reverse(
                'wiki.document',
                kwargs={'document_path': revision.document.slug}
            )
            assert document_url in table_row_text

    def test_spam_trends_show(self, mock_analytics_upageviews):
        """The spam trends table shows up."""
        self.client.login(username='admin', password='testpass')
        # The first response will say that the report is being processed
        response = self.client.get(reverse('dashboards.spam'))
        assert 200 == response.status_code

        response2 = self.client.get(reverse('dashboards.spam'))
        page = pq(response2.content)
        spam_trends_table = page.find('.spam-trends-table')
        assert 1 == len(spam_trends_table)

    def test_spam_trends_stats(self, mock_analytics_upageviews):
        """Test that the correct stats show up on the spam trends dashboard."""
        # Period length
        days_in_week = 7
        days_in_month = 28
        days_in_quarter = 91
        # Dates
        today = datetime.datetime.today()
        yesterday = today - datetime.timedelta(days=1)
        three_days_ago = today - datetime.timedelta(days=3)
        weekly_start_date = today - datetime.timedelta(days=days_in_week)
        ten_days_ago = today - datetime.timedelta(days=10)
        monthly_start_date = today - datetime.timedelta(days=days_in_month)
        thirtyfive_days_ago = today - datetime.timedelta(days=35)
        quarterly_start_date = today - datetime.timedelta(days=days_in_quarter)
        hundred_days_ago = today - datetime.timedelta(days=100)

        # Revisions made by self.testuser: 3 made today, 3 made 3 days ago,
        # 3 made 10 days ago, 3 made 35 days ago, 3 made 100 days ago
        revs = self.create_revisions(num=15, creator=self.testuser, document=self.document)
        for i in range(0, 3):
            revs[i].created = today
        for i in range(3, 6):
            revs[i].created = three_days_ago
        for i in range(6, 9):
            revs[i].created = ten_days_ago
        for i in range(9, 12):
            revs[i].created = thirtyfive_days_ago
        for i in range(12, 15):
            revs[i].created = hundred_days_ago
        for rev in revs:
            rev.save()

        # Published spam by self.testuser
        spam_rev_today = revs[2]
        spam_rev_3_days_ago = revs[5]
        spam_rev_10_days_ago = revs[8]
        spam_rev_35_days_ago = revs[11]
        spam_rev_100_days_ago = revs[14]
        spam_revs = [spam_rev_today, spam_rev_3_days_ago, spam_rev_10_days_ago,
                     spam_rev_35_days_ago, spam_rev_100_days_ago]
        # Summary of spam submissions
        spam_weekly = [spam_rev_3_days_ago]
        spam_monthly = [spam_rev_3_days_ago, spam_rev_10_days_ago]
        spam_quarterly = [spam_rev_3_days_ago, spam_rev_10_days_ago,
                          spam_rev_35_days_ago]
        # All of the spam_revs were published and then marked as spam
        for rev in spam_revs:
            rev.save()
            rev.akismet_submissions.create(sender=self.admin, type="spam")

        # Summary of self.testuser's ham submissions
        ham_weekly = revs[3:5]
        ham_monthly = revs[3:5] + revs[6:8]
        ham_quarterly = revs[3:5] + revs[6:8] + revs[9:11]

        # There were 2 correctly blocked spam attempts 3 days ago (within past week)
        true_blocked_spam_num = 2
        for i in range(0, true_blocked_spam_num):
            document_spam_rev_3_days_ago = DocumentSpamAttempt(
                user=self.testuser,
                title='A spam revision',
                slug='spam-revision-slug',
                document=self.document,
                review=DocumentSpamAttempt.SPAM
            )
            document_spam_rev_3_days_ago.save()
            document_spam_rev_3_days_ago.created = three_days_ago
            document_spam_rev_3_days_ago.save()

        # There was 1 incorrectly blocked spam attempt 3 days ago
        false_blocked_spam_num = 1
        for i in range(0, false_blocked_spam_num):
            document_ham_rev_3_days_ago = DocumentSpamAttempt(
                user=self.testuser,
                title='Not a spam revision',
                slug='ham-revision-slug',
                document=self.document,
                review=DocumentSpamAttempt.HAM
            )
            document_ham_rev_3_days_ago.save()
            document_ham_rev_3_days_ago.created = three_days_ago
            document_ham_rev_3_days_ago.save()

        page_views = {}
        # The spam from 3 days ago was seen 3 times, from 10 days ago see 10 times,
        # and from 35 days ago seen 35 times
        page_views[spam_rev_3_days_ago.id] = 3
        page_views[spam_rev_10_days_ago.id] = 10
        page_views[spam_rev_35_days_ago.id] = 35
        # The mock Google Analytics return values for page views
        mock_analytics_upageviews.return_value = page_views

        self.client.login(username='admin', password='testpass')
        # The first response will say that the report is being processed
        response = self.client.get(reverse('dashboards.spam'))
        assert 200 == response.status_code

        response2 = self.client.get(reverse('dashboards.spam'))
        page = pq(response2.content)

        row_daily = page.find('.spam-trends-table tbody tr')[0].text_content().replace(' ', '').strip('\n').split('\n')
        row_weekly = page.find('.spam-trends-table tbody tr')[1].text_content().replace(' ', '').strip('\n').split('\n')
        row_monthly = page.find('.spam-trends-table tbody tr')[2].text_content().replace(' ', '').strip('\n').split('\n')
        row_quarterly = page.find('.spam-trends-table tbody tr')[3].text_content().replace(' ', '').strip('\n').split('\n')

        # These are the columns in the spam dashboard spam trends table
        period = 0
        start_date = 1
        spam_viewers_change_percent = 2
        spam_viewers = 3
        daily_average_viewers = 4
        published_spam = 5
        blocked_spam = 6
        blocked_ham = 7
        true_positive_rate = 8
        true_negative_rate = 9

        # The periods are identified as 'Daily', 'Weekly', 'Monthly', 'Quarterly'
        assert 'Daily' == row_daily[period]
        assert 'Weekly' == row_weekly[period]
        assert 'Monthly' == row_monthly[period]
        assert 'Quarterly' == row_quarterly[period]
        # The start dates for each period are correct
        assert yesterday.strftime('%Y-%m-%d') == row_daily[start_date]
        assert weekly_start_date.strftime('%Y-%m-%d') == row_weekly[start_date]
        assert monthly_start_date.strftime('%Y-%m-%d') == row_monthly[start_date]
        assert quarterly_start_date.strftime('%Y-%m-%d') == row_quarterly[start_date]
        # The page views during the week, month, quarter
        spam_views_week = page_views[spam_rev_3_days_ago.id]
        spam_views_month = spam_views_week + page_views[spam_rev_10_days_ago.id]
        spam_views_month_exclude_week = page_views[spam_rev_10_days_ago.id]
        spam_views_quarter = spam_views_month + page_views[spam_rev_35_days_ago.id]
        spam_views_quarter_exclude_month = page_views[spam_rev_35_days_ago.id]
        # The percentage change in spam viewers
        weekly_spam_change_percent = '{:.1%}'.format(
            float(spam_views_week - spam_views_month_exclude_week) / spam_views_month_exclude_week
        )
        monthly_spam_change_percent = '{:.1%}'.format(
            float(spam_views_month - spam_views_quarter_exclude_month) / spam_views_quarter_exclude_month
        )
        assert '0.0%' == row_daily[spam_viewers_change_percent]
        assert weekly_spam_change_percent == row_weekly[spam_viewers_change_percent]
        assert monthly_spam_change_percent == row_monthly[spam_viewers_change_percent]
        assert '0.0%' == row_quarterly[spam_viewers_change_percent]
        # The spam viewers
        assert 0 == int(row_daily[spam_viewers])
        assert spam_views_week == int(row_weekly[spam_viewers])
        assert spam_views_month == int(row_monthly[spam_viewers])
        assert spam_views_quarter == int(row_quarterly[spam_viewers])
        # The daily average of spam viewers
        assert float(row_daily[daily_average_viewers]) == 0.0
        assert (row_weekly[daily_average_viewers] ==
                '{:.1f}'.format(float(spam_views_week) / days_in_week))
        assert (row_monthly[daily_average_viewers] ==
                '{:.1f}'.format(float(spam_views_month) / days_in_month))
        assert (row_quarterly[daily_average_viewers] ==
                '{:.1f}'.format(float(spam_views_quarter) / days_in_quarter))
        # The published spam: 1 this week, 2 this month, 3 this quarter
        assert not int(row_daily[published_spam])
        assert len(spam_weekly) == int(row_weekly[published_spam])
        assert len(spam_monthly) == int(row_monthly[published_spam])
        assert len(spam_quarterly) == int(row_quarterly[published_spam])
        # The blocked spam: there were 2 correctly blocked spam attempts 3 days ago
        assert 0 == int(row_daily[blocked_spam])
        assert true_blocked_spam_num == int(row_weekly[blocked_spam])
        assert true_blocked_spam_num == int(row_monthly[blocked_spam])
        assert true_blocked_spam_num == int(row_quarterly[blocked_spam])
        # The blocked ham: there was 1 incorrectly blocked spam attempt 3 days ago
        assert 0 == int(row_daily[blocked_ham])
        assert false_blocked_spam_num == int(row_weekly[blocked_ham])
        assert false_blocked_spam_num == int(row_monthly[blocked_ham])
        assert false_blocked_spam_num == int(row_quarterly[blocked_ham])
        # The true positive rate == blocked_spam / total spam
        tpr_weekly = '{:.1%}'.format(
            true_blocked_spam_num / float(true_blocked_spam_num + len(spam_weekly))
        )
        tpr_monthly = '{:.1%}'.format(
            true_blocked_spam_num / float(true_blocked_spam_num + len(spam_monthly))
        )
        tpr_quarterly = '{:.1%}'.format(
            true_blocked_spam_num / float(true_blocked_spam_num + len(spam_quarterly))
        )
        assert '100.0%' == row_daily[true_positive_rate]
        assert tpr_weekly == row_weekly[true_positive_rate]
        assert tpr_monthly == row_monthly[true_positive_rate]
        assert tpr_quarterly == row_quarterly[true_positive_rate]
        # The true negative rate == published ham / total ham
        tnr_weekly = '{:.1%}'.format(
            len(ham_weekly) / float(false_blocked_spam_num + len(ham_weekly))
        )
        tnr_monthly = '{:.1%}'.format(
            len(ham_monthly) / float(false_blocked_spam_num + len(ham_monthly))
        )
        tnr_quarterly = '{:.1%}'.format(
            len(ham_quarterly) / float(false_blocked_spam_num + len(ham_quarterly))
        )
        assert '100.0%' == row_daily[true_negative_rate]
        assert tnr_weekly == row_weekly[true_negative_rate]
        assert tnr_monthly == row_monthly[true_negative_rate]
        assert tnr_quarterly == row_quarterly[true_negative_rate]


@pytest.mark.parametrize(
    'http_method', ['put', 'post', 'delete', 'options', 'head'])
@pytest.mark.parametrize(
    'endpoint', ['revisions', 'user_lookup', 'topic_lookup', 'spam', 'macros'])
def test_disallowed_methods(db, client, http_method, endpoint):
    """HTTP methods other than GET & HEAD are not allowed."""
    url = reverse('dashboards.{}'.format(endpoint))
    response = getattr(client, http_method)(url)
    assert response.status_code == 405
    if endpoint in ('spam', 'revisions'):
        assert_no_cache_header(response)
    else:
        assert_shared_cache_header(response)
        if endpoint in ('user_lookup', 'topic_lookup'):
            assert 'Vary' in response
            assert 'X-Requested-With' in response['Vary']


@pytest.mark.parametrize('mode', ['ajax', 'non-ajax'])
@pytest.mark.parametrize('endpoint', ['user_lookup', 'topic_lookup'])
def test_lookup(root_doc, wiki_user_2, wiki_user_3, client, mode, endpoint):
    qs, headers = '', {}
    if mode == 'ajax':
        if endpoint == 'topic_lookup':
            qs = '?topic=root'
            expected_content = [{'label': 'Root'}]
        else:
            qs = '?user=wiki'
            expected_content = [{'label': 'wiki_user'},
                                {'label': 'wiki_user_2'},
                                {'label': 'wiki_user_3'}]
        headers.update(HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    else:
        expected_content = []
    url = reverse('dashboards.{}'.format(endpoint)) + qs
    response = client.get(url, **headers)
    assert response.status_code == 200
    assert 'X-Requested-With' in response['Vary']
    assert_shared_cache_header(response)
    assert response['Content-Type'] == 'application/json; charset=utf-8'
    assert json.loads(response.content) == expected_content


@mock.patch('kuma.dashboards.views.macro_usage')
def test_macros(mock_usage, client, db):
    """The normal macro page is a three-column table."""
    mock_usage.return_value = {
        'A11yRoleQuicklinks': {
            'github_subpath': 'A11yRoleQuicklinks.ejs',
            'count': 100,
            'en_count': 50,
        }
    }

    response = client.get(reverse('dashboards.macros'))
    assert response.status_code == 200
    assert 'Cookie' in response['Vary']
    assert_shared_cache_header(response)
    assert "Found 1 active macro." in response.content.decode('utf8')
    page = pq(response.content)
    assert len(page("table.macros-table")) == 1
    assert len(page("th.stat-header")) == 2


@mock.patch('kuma.dashboards.views.macro_usage')
def test_macros_no_counts(mock_usage, client, db):
    """The macro page is a one-column table when counts are unavailable."""
    mock_usage.return_value = {
        'A11yRoleQuicklinks': {
            'github_subpath': 'A11yRoleQuicklinks.ejs',
            'count': 0,
            'en_count': 0,
        },
        'CSSRef': {
            'github_subpath': 'CSSRef.ejs',
            'count': 0,
            'en_count': 0,
        }
    }

    response = client.get(reverse('dashboards.macros'))
    assert response.status_code == 200
    assert "Found 2 active macros." in response.content.decode('utf8')
    page = pq(response.content)
    assert len(page("table.macros-table")) == 1
    assert len(page("th.stat-header")) == 0


def test_index(client, db):
    """The dashboard index can be loaded."""
    response = client.get(reverse('dashboards.index'))
    assert response.status_code == 200
    content = response.content.decode(response.charset)
    assert reverse('dashboards.macros') in content
    assert reverse('dashboards.spam') not in content
    l10n_url = reverse('wiki.list_with_localization_tag',
                       kwargs={'tag': 'inprogress'})
    assert l10n_url not in content


def test_index_non_english_sees_translations(client, db):
    """Non-English users see the in-progress translations dashboard."""
    with override('fr'):
        response = client.get(reverse('dashboards.index'))
        assert response.status_code == 200
        content = response.content.decode(response.charset)
        assert reverse('dashboards.macros') in content
        assert reverse('dashboards.spam') not in content
        l10n_url = reverse('wiki.list_with_localization_tag',
                           kwargs={'tag': 'inprogress'})
        assert l10n_url in content


def test_index_admin_sees_spam_dashboard(admin_client):
    """A moderator can see the spam dashboard in the list."""
    response = admin_client.get(reverse('dashboards.index'))
    assert response.status_code == 200
    content = response.content.decode(response.charset)
    assert reverse('dashboards.macros') in content
    assert reverse('dashboards.spam') in content
    l10n_url = reverse('wiki.list_with_localization_tag',
                       kwargs={'tag': 'inprogress'})
    assert l10n_url not in content
