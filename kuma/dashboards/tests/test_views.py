import datetime
import json

import mock
import pytest
from django.contrib.auth.models import Permission
from django.core.exceptions import ImproperlyConfigured
from pyquery import PyQuery as pq
from waffle.models import Flag, Switch

from kuma.core.tests import (assert_no_cache_header,
                             assert_shared_cache_header, eq_, ok_)
from kuma.core.urlresolvers import reverse
from kuma.core.utils import to_html, urlparams
from kuma.dashboards.forms import RevisionDashboardForm
from kuma.spam.constants import SPAM_SUBMISSIONS_FLAG
from kuma.users.models import User, UserBan
from kuma.users.tests import create_document, SampleRevisionsMixin, UserTestCase
from kuma.wiki.models import DocumentSpamAttempt, RevisionAkismetSubmission


@pytest.mark.dashboards
class RevisionsDashTest(UserTestCase):
    fixtures = UserTestCase.fixtures + ['wiki/documents.json']

    def test_main_view(self):
        response = self.client.get(reverse('dashboards.revisions',
                                           locale='en-US'))
        assert response.status_code == 200
        assert 'Vary' in response
        assert 'X-Requested-With' in response['Vary']
        assert 'Cache-Control' in response
        assert_shared_cache_header(response)
        assert 'text/html' in response['Content-Type']
        assert ('dashboards/revisions.html' in
                (template.name for template in response.templates))

    def test_main_view_with_banned_user(self):
        testuser = User.objects.get(username='testuser')
        admin = User.objects.get(username='admin')
        ban = UserBan(user=testuser, by=admin, reason='Testing')
        ban.save()

        self.client.login(username='admin', password='testpass')
        response = self.client.get(reverse('dashboards.revisions',
                                           locale='en-US'))
        eq_(200, response.status_code)

    def test_revision_list(self):
        url = reverse('dashboards.revisions', locale='en-US')
        # We only get revisions when requesting via AJAX.
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        eq_(response.status_code, 200)

        page = pq(response.content)
        revisions = page.find('.dashboard-row')

        eq_(revisions.length, 11)

        # Most recent revision first.
        eq_(int(pq(revisions[0]).attr('data-revision-id')), 30)
        # Second-most-recent revision next.
        eq_(int(pq(revisions[1]).attr('data-revision-id')), 29)
        # Oldest revision last.
        eq_(int(pq(revisions[-1]).attr('data-revision-id')), 19)

    def test_ip_link_on_switch(self):
        url = reverse('dashboards.revisions', locale='en-US')
        response = self.client.get(url)
        eq_(200, response.status_code)

        page = pq(response.content)
        ip_button = page.find('button#show_ips_btn')
        eq_([], ip_button)

        Switch.objects.create(name='store_revision_ips', active=True)
        self.client.login(username='admin', password='testpass')
        url = reverse('dashboards.revisions', locale='en-US')
        response = self.client.get(url)
        eq_(200, response.status_code)

        page = pq(response.content)
        ip_button = page.find('button#show_ips_btn')
        ok_(len(ip_button) > 0)

    def test_spam_submission_buttons(self):
        url = reverse('dashboards.revisions', locale='en-US')
        response = self.client.get(url)
        eq_(200, response.status_code)

        page = pq(response.content)
        spam_report_button = page.find('.spam-ham-button')
        eq_(spam_report_button, [])

        flag = Flag.objects.create(name=SPAM_SUBMISSIONS_FLAG)
        flag.users.add(User.objects.get(username='admin'))
        self.client.login(username='admin', password='testpass')
        url = reverse('dashboards.revisions', locale='en-US')
        response = self.client.get(url)
        eq_(200, response.status_code)

        page = pq(response.content)
        spam_report_button = page.find('.spam-ham-button')
        # Revisions available, admin has privileges to see this
        ok_(len(spam_report_button) > 0)

    def test_locale_filter(self):
        url = urlparams(reverse('dashboards.revisions', locale='fr'),
                        locale='fr')
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        eq_(200, response.status_code)

        page = pq(response.content)
        revisions = page.find('.dashboard-row')

        ok_(len(revisions))
        eq_(1, revisions.length)

        ok_('fr' in to_html(pq(revisions[0]).find('.locale')))

    def test_creator_filter(self):
        url = urlparams(reverse('dashboards.revisions', locale='en-US'),
                        user='testuser01')
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        eq_(200, response.status_code)

        page = pq(response.content)
        revisions = page.find('.dashboard-row')

        eq_(2, revisions.length)

        for revision in revisions:
            author = pq(revision).find('.dashboard-author').text()
            ok_('testuser01' in author)
            ok_('testuser2' not in author)

    def test_topic_filter(self):
        url = urlparams(reverse('dashboards.revisions', locale='en-US'),
                        topic='article-with-revisions')
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        eq_(response.status_code, 200)

        page = pq(response.content)
        revisions = page.find('.dashboard-row')

        eq_(revisions.length, 7)
        for revision in revisions:
            ok_('lorem' not in to_html(pq(revision).find('.dashboard-title')))

    def test_known_authors_lookup(self):
        # Only testuser01 is in the Known Authors group
        url = urlparams(reverse('dashboards.revisions', locale='en-US'),
                        authors=RevisionDashboardForm.KNOWN_AUTHORS)
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        eq_(200, response.status_code)

        page = pq(response.content)
        revisions = page.find('.dashboard-row')

        for revision in revisions:
            author = to_html(pq(revision).find('.dashboard-author'))
            ok_('testuser01' in author)
            ok_('testuser2' not in author)

    def test_known_authors_filter(self):
        # There are a total of 11 revisions
        url = urlparams(reverse('dashboards.revisions', locale='en-US'),
                        authors=RevisionDashboardForm.ALL_AUTHORS)
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        eq_(response.status_code, 200)

        page = pq(response.content)
        revisions = page.find('.dashboard-row')

        eq_(11, revisions.length)

        # Only testuser01 is in the Known Authors group, and has 2 revisions
        url = urlparams(reverse('dashboards.revisions', locale='en-US'),
                        authors=RevisionDashboardForm.KNOWN_AUTHORS)
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        eq_(response.status_code, 200)

        page = pq(response.content)
        revisions = page.find('.dashboard-row')

        eq_(2, revisions.length)

        # Of the 11 revisions, 9 are by users not in the Known Authors group
        url = urlparams(reverse('dashboards.revisions', locale='en-US'),
                        authors=RevisionDashboardForm.UNKNOWN_AUTHORS)
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        eq_(response.status_code, 200)

        page = pq(response.content)
        revisions = page.find('.dashboard-row')

        eq_(9, revisions.length)

    def test_known_authors_filter_ignored_with_username(self):
        """When user filters by username, the Known Authors filter is ignored"""
        # Only testuser01 is in the Known Authors group, and has 2 revisions
        # Filtering by testuser2 should return testuser2's revisions (5 of them)
        # and ignore the "Known Authors" filter
        url = urlparams(reverse('dashboards.revisions', locale='en-US'),
                        user='testuser2', authors=RevisionDashboardForm.KNOWN_AUTHORS)
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        eq_(response.status_code, 200)

        page = pq(response.content)
        revisions = page.find('.dashboard-row')

        eq_(5, revisions.length)


@mock.patch('kuma.dashboards.utils.analytics_upageviews')
class SpamDashTest(SampleRevisionsMixin, UserTestCase):
    fixtures = UserTestCase.fixtures + ['wiki/documents.json']

    def test_not_logged_in(self, mock_analytics_upageviews):
        """A user who is not logged in is not able to see the dashboard."""
        response = self.client.get(reverse('dashboards.spam',
                                           locale='en-US'))
        assert response.status_code == 302
        assert_no_cache_header(response)

    def test_permissions(self, mock_analytics_upageviews):
        """A user with correct permissions is able to see the dashboard."""
        self.client.login(username='testuser', password='testpass')
        # Attempt to see spam dashboard as a logged-in user without permissions
        response = self.client.get(reverse('dashboards.spam',
                                           locale='en-US'))
        assert response.status_code == 403

        # Give testuser wiki.add_revisionakismetsubmission permission
        perm_akismet = Permission.objects.get(codename='add_revisionakismetsubmission')
        self.testuser.user_permissions.add(perm_akismet)
        response = self.client.get(reverse('dashboards.spam',
                                           locale='en-US'))
        assert response.status_code == 403

        # Give testuser wiki.add_documentspamattempt permission
        perm_spam = Permission.objects.get(codename='add_documentspamattempt')
        self.testuser.user_permissions.add(perm_spam)
        response = self.client.get(reverse('dashboards.spam',
                                           locale='en-US'))
        assert response.status_code == 403

        # Give testuser wiki.add_userban permission
        perm_ban = Permission.objects.get(codename='add_userban')
        self.testuser.user_permissions.add(perm_ban)
        response = self.client.get(reverse('dashboards.spam',
                                           locale='en-US'))
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
        response = self.client.get(reverse('dashboards.spam', locale='en-US'))
        eq_(200, response.status_code)

        response2 = self.client.get(reverse('dashboards.spam', locale='en-US'))

        self.assertContains(response2, "Oops!", status_code=200)
        page = pq(response2.content)
        spam_trends_table = page.find('.spam-trends-table')
        eq_(len(spam_trends_table), 1)
        spam_events_table = page.find('.spam-events-table')
        eq_(len(spam_events_table), 1)

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
            revision.akismet_submissions.add(RevisionAkismetSubmission(
                sender=self.admin, type="spam")
            )
        # self.admin creates some revisions on a different document
        self.create_revisions(num=3, creator=self.admin)

        mock_analytics_upageviews.return_value = {
            rev_doc0[0].id: 0,
            rev_doc1[0].id: 0,
            rev_doc2[0].id: 0
        }

        self.client.login(username='admin', password='testpass')
        # The first response will say that the report is being processed
        response = self.client.get(reverse('dashboards.spam', locale='en-US'))
        eq_(200, response.status_code)

        response2 = self.client.get(reverse('dashboards.spam', locale='en-US'))
        page = pq(response2.content)
        table_rows = page.find('.spam-events-table tbody tr')
        table_row_text = ''
        for table_row in table_rows:
            table_row_text += table_row.text_content()

        eq_(len(table_rows), len(created_revisions))
        for revision in created_revisions:
            document_url = reverse(
                'wiki.document',
                kwargs={'document_path': revision.document.slug}
            )
            ok_(document_url in table_row_text)

    def test_spam_trends_show(self, mock_analytics_upageviews):
        """The spam trends table shows up."""
        self.client.login(username='admin', password='testpass')
        # The first response will say that the report is being processed
        response = self.client.get(reverse('dashboards.spam', locale='en-US'))
        eq_(200, response.status_code)

        response2 = self.client.get(reverse('dashboards.spam', locale='en-US'))
        page = pq(response2.content)
        spam_trends_table = page.find('.spam-trends-table')
        eq_(len(spam_trends_table), 1)

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
            rev.akismet_submissions.add(RevisionAkismetSubmission(
                sender=self.admin, type="spam")
            )

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
        response = self.client.get(reverse('dashboards.spam', locale='en-US'))
        eq_(200, response.status_code)

        response2 = self.client.get(reverse('dashboards.spam', locale='en-US'))
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
        eq_(row_daily[period], 'Daily')
        eq_(row_weekly[period], 'Weekly')
        eq_(row_monthly[period], 'Monthly')
        eq_(row_quarterly[period], 'Quarterly')
        # The start dates for each period are correct
        eq_(row_daily[start_date], yesterday.strftime('%Y-%m-%d'))
        eq_(row_weekly[start_date], weekly_start_date.strftime('%Y-%m-%d'))
        eq_(row_monthly[start_date], monthly_start_date.strftime('%Y-%m-%d'))
        eq_(row_quarterly[start_date], quarterly_start_date.strftime('%Y-%m-%d'))
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
        eq_(row_daily[spam_viewers_change_percent], '0.0%')
        eq_(row_weekly[spam_viewers_change_percent], weekly_spam_change_percent)
        eq_(row_monthly[spam_viewers_change_percent], monthly_spam_change_percent)
        eq_(row_quarterly[spam_viewers_change_percent], '0.0%')
        # The spam viewers
        eq_(int(row_daily[spam_viewers]), 0)
        eq_(int(row_weekly[spam_viewers]), spam_views_week)
        eq_(int(row_monthly[spam_viewers]), spam_views_month)
        eq_(int(row_quarterly[spam_viewers]), spam_views_quarter)
        # The daily average of spam viewers
        eq_(float(row_daily[daily_average_viewers]), 0.0)
        eq_(row_weekly[daily_average_viewers],
            '{:.1f}'.format(float(spam_views_week) / days_in_week))
        eq_(row_monthly[daily_average_viewers],
            '{:.1f}'.format(float(spam_views_month) / days_in_month))
        eq_(row_quarterly[daily_average_viewers],
            '{:.1f}'.format(float(spam_views_quarter) / days_in_quarter))
        # The published spam: 1 this week, 2 this month, 3 this quarter
        eq_(int(row_daily[published_spam]), len([]))
        eq_(int(row_weekly[published_spam]), len(spam_weekly))
        eq_(int(row_monthly[published_spam]), len(spam_monthly))
        eq_(int(row_quarterly[published_spam]), len(spam_quarterly))
        # The blocked spam: there were 2 correctly blocked spam attempts 3 days ago
        eq_(int(row_daily[blocked_spam]), 0)
        eq_(int(row_weekly[blocked_spam]), true_blocked_spam_num)
        eq_(int(row_monthly[blocked_spam]), true_blocked_spam_num)
        eq_(int(row_quarterly[blocked_spam]), true_blocked_spam_num)
        # The blocked ham: there was 1 incorrectly blocked spam attempt 3 days ago
        eq_(int(row_daily[blocked_ham]), 0)
        eq_(int(row_weekly[blocked_ham]), false_blocked_spam_num)
        eq_(int(row_monthly[blocked_ham]), false_blocked_spam_num)
        eq_(int(row_quarterly[blocked_ham]), false_blocked_spam_num)
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
        eq_(row_daily[true_positive_rate], '100.0%')
        eq_(row_weekly[true_positive_rate], tpr_weekly)
        eq_(row_monthly[true_positive_rate], tpr_monthly)
        eq_(row_quarterly[true_positive_rate], tpr_quarterly)
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
        eq_(row_daily[true_negative_rate], '100.0%')
        eq_(row_weekly[true_negative_rate], tnr_weekly)
        eq_(row_monthly[true_negative_rate], tnr_monthly)
        eq_(row_quarterly[true_negative_rate], tnr_quarterly)


@pytest.mark.parametrize(
    'http_method', ['put', 'post', 'delete', 'options', 'head'])
@pytest.mark.parametrize(
    'endpoint', ['revisions', 'user_lookup', 'topic_lookup', 'spam', 'macros'])
def test_disallowed_methods(db, client, http_method, endpoint):
    """HTTP methods other than GET & HEAD are not allowed."""
    url = reverse('dashboards.{}'.format(endpoint), locale='en-US')
    response = getattr(client, http_method)(url)
    assert response.status_code == 405
    if endpoint == 'spam':
        assert_no_cache_header(response)
    else:
        assert_shared_cache_header(response)
        if endpoint in ('revisions', 'user_lookup', 'topic_lookup'):
            assert 'Vary' in response
            assert 'X-Requested-With' in response['Vary']


@pytest.mark.parametrize('mode', ['ajax', 'non-ajax'])
@pytest.mark.parametrize('endpoint', ['user_lookup', 'topic_lookup'])
def test_lookup(root_doc, wiki_user_2, wiki_user_3, client, mode, endpoint):
    qs, headers = '', {}
    if mode == 'ajax':
        if endpoint == 'topic_lookup':
            qs = '?topic=root'
            expected_content = [{u'label': u'Root'}]
        else:
            qs = '?user=wiki'
            expected_content = [{u'label': u'wiki_user'},
                                {u'label': u'wiki_user_2'},
                                {u'label': u'wiki_user_3'}]
        headers.update(HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    else:
        expected_content = []
    url = reverse('dashboards.{}'.format(endpoint), locale='en-US') + qs
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

    response = client.get(reverse('dashboards.macros'), follow=True)
    assert response.status_code == 200
    assert 'Cookie' in response['Vary']
    assert_shared_cache_header(response)
    assert "Found 1 active macro." in response.content
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

    response = client.get(reverse('dashboards.macros'), follow=True)
    assert response.status_code == 200
    assert "Found 2 active macros." in response.content
    page = pq(response.content)
    assert len(page("table.macros-table")) == 1
    assert len(page("th.stat-header")) == 0
