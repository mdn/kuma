import json
import os
from urlparse import parse_qs, urlparse

import mock
import pytest
import requests_mock
from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount, SocialApp
from allauth.socialaccount.providers import registry
from allauth.tests import MockedResponse, mocked_response
from constance.test.utils import override_config
from django.conf import settings
from django.contrib.auth.hashers import UNUSABLE_PASSWORD_PREFIX
from django.contrib.sites.models import Site
from django.core.paginator import PageNotAnInteger
from pyquery import PyQuery as pq
from waffle.models import Flag

from kuma.core.tests import eq_, ok_
from kuma.core.urlresolvers import reverse
from kuma.spam.akismet import Akismet
from kuma.spam.constants import SPAM_SUBMISSIONS_FLAG, SPAM_URL, VERIFY_URL
from kuma.wiki.models import RevisionAkismetSubmission

from . import SampleRevisionsMixin, UserTestCase, email, user
from ..models import UserBan
from ..providers.github.provider import KumaGitHubProvider
from ..signup import SignupForm


TESTUSER_PASSWORD = 'testpass'


class OldProfileTestCase(UserTestCase):
    localizing_client = True

    def test_old_profile_url_gone(self):
        response = self.client.get('/users/edit', follow=True)
        eq_(404, response.status_code)


@pytest.mark.bans
class BanTestCase(UserTestCase):
    localizing_client = True

    def test_ban_permission(self):
        """The ban permission controls access to the ban view."""
        admin = self.user_model.objects.get(username='admin')
        testuser = self.user_model.objects.get(username='testuser')

        # testuser doesn't have ban permission, can't ban.
        self.client.login(username='testuser',
                          password='testpass')
        ban_url = reverse('users.ban_user',
                          kwargs={'user_id': admin.id})
        resp = self.client.get(ban_url)
        eq_(302, resp.status_code)
        ok_(str(settings.LOGIN_URL) in resp['Location'])
        self.client.logout()

        # admin has ban permission, can ban.
        self.client.login(username='admin',
                          password='testpass')
        ban_url = reverse('users.ban_user',
                          kwargs={'user_id': testuser.id})
        resp = self.client.get(ban_url)
        eq_(200, resp.status_code)

    def test_ban_view(self):
        testuser = self.user_model.objects.get(username='testuser')
        admin = self.user_model.objects.get(username='admin')

        self.client.login(username='admin', password='testpass')

        data = {'reason': 'Banned by unit test.'}
        ban_url = reverse('users.ban_user',
                          kwargs={'user_id': testuser.id})

        resp = self.client.post(ban_url, data)
        eq_(302, resp.status_code)
        ok_(testuser.get_absolute_url() in resp['Location'])

        testuser_banned = self.user_model.objects.get(username='testuser')
        ok_(not testuser_banned.is_active)

        bans = UserBan.objects.filter(user=testuser,
                                      by=admin,
                                      reason='Banned by unit test.')
        ok_(bans.count())

    def test_ban_nonexistent_user(self):
        # Attempting to ban a non-existent user should 404
        admin = self.user_model.objects.get(username='admin')

        self.client.login(username='admin', password='testpass')

        nonexistent_user_id = self.user_model.objects.last().id + 1
        data = {'reason': 'Banned by unit test.'}
        ban_url = reverse('users.ban_user',
                          kwargs={'user_id': nonexistent_user_id})

        resp = self.client.post(ban_url, data)
        eq_(404, resp.status_code)

        bans = UserBan.objects.filter(user__id=nonexistent_user_id,
                                      by=admin,
                                      reason='Banned by unit test.')
        eq_(bans.count(), 0)

    def test_ban_without_reason(self):
        # Attempting to ban without a reason should return the form
        testuser = self.user_model.objects.get(username='testuser')
        admin = self.user_model.objects.get(username='admin')

        self.client.login(username='admin', password='testpass')

        ban_url = reverse('users.ban_user',
                          kwargs={'user_id': testuser.id})

        # POST without data kwargs
        resp = self.client.post(ban_url)

        eq_(200, resp.status_code)

        bans = UserBan.objects.filter(user=testuser,
                                      by=admin,
                                      reason='Banned by unit test.')
        eq_(bans.count(), 0)

        # POST with a blank reason
        data = {'reason': ''}
        resp = self.client.post(ban_url, data)

        eq_(200, resp.status_code)

        bans = UserBan.objects.filter(user=testuser,
                                      by=admin,
                                      reason='Banned by unit test.')
        eq_(bans.count(), 0)

    def test_bug_811751_banned_user(self):
        """A banned user should not be viewable"""
        testuser = self.user_model.objects.get(username='testuser')
        url = reverse('users.user_detail', args=(testuser.username,))

        # User viewable if not banned
        response = self.client.get(url, follow=True)
        self.assertNotEqual(response.status_code, 403)

        # Ban User
        admin = self.user_model.objects.get(username='admin')
        testuser = self.user_model.objects.get(username='testuser')
        UserBan.objects.create(user=testuser, by=admin,
                               reason='Banned by unit test.',
                               is_active=True)

        # User not viewable if banned
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 403)

        # Admin can view banned user
        self.client.login(username='admin', password='testpass')
        response = self.client.get(url, follow=True)
        self.assertNotEqual(response.status_code, 403)

    def test_get_ban_user_view(self):
        # For an unbanned user get the ban_user view
        testuser = self.user_model.objects.get(username='testuser')
        admin = self.user_model.objects.get(username='admin')

        self.client.login(username='admin', password='testpass')
        ban_url = reverse('users.ban_user',
                          kwargs={'user_id': testuser.id})

        resp = self.client.get(ban_url)
        eq_(200, resp.status_code)

        # For a banned user redirect to user detail page
        UserBan.objects.create(user=testuser, by=admin,
                               reason='Banned by unit test.',
                               is_active=True)
        resp = self.client.get(ban_url)
        eq_(302, resp.status_code)
        ok_(testuser.get_absolute_url() in resp['Location'])


@pytest.mark.bans
class BanAndCleanupTestCase(UserTestCase):
    localizing_client = True

    def test_ban_permission(self):
        """The ban permission controls access to the ban and cleanup view."""
        admin = self.user_model.objects.get(username='admin')
        testuser = self.user_model.objects.get(username='testuser')

        # testuser doesn't have ban permission, can't ban.
        self.client.login(username='testuser',
                          password='testpass')
        ban_url = reverse('users.ban_user_and_cleanup',
                          kwargs={'user_id': admin.id})
        resp = self.client.get(ban_url)
        eq_(302, resp.status_code)
        ok_(str(settings.LOGIN_URL) in resp['Location'])
        self.client.logout()

        # admin has ban permission, can ban.
        self.client.login(username='admin',
                          password='testpass')
        ban_url = reverse('users.ban_user_and_cleanup',
                          kwargs={'user_id': testuser.id})
        resp = self.client.get(ban_url)
        eq_(200, resp.status_code)

    def test_ban_nonexistent_user(self):
        """GETs to ban_user_and_cleanup for nonexistent user return 404."""
        testuser = self.user_model.objects.get(username='testuser')

        # GET request
        self.client.login(username='admin',
                          password='testpass')
        ban_url = reverse('users.ban_user_and_cleanup',
                          kwargs={'user_id': testuser.id})
        testuser.delete()
        resp = self.client.get(ban_url)
        eq_(404, resp.status_code)


@pytest.mark.bans
class BanUserAndCleanupSummaryTestCase(SampleRevisionsMixin, UserTestCase):
    localizing_client = True

    def setUp(self):
        super(BanUserAndCleanupSummaryTestCase, self).setUp()

        self.ban_testuser_url = reverse('users.ban_user_and_cleanup_summary',
                                        kwargs={'user_id': self.testuser.id})
        self.ban_testuser2_url = reverse('users.ban_user_and_cleanup_summary',
                                         kwargs={'user_id': self.testuser2.id})
        self.client.login(username='admin', password='testpass')

    def test_ban_nonexistent_user(self):
        """POSTs to ban_user_and_cleanup for nonexistent user return 404."""
        self.testuser.delete()
        resp = self.client.post(self.ban_testuser_url)
        eq_(404, resp.status_code)

    def test_post_returns_summary_page(self):
        """POSTing to ban_user_and_cleanup returns the summary page."""
        resp = self.client.post(self.ban_testuser_url)
        eq_(200, resp.status_code)

    def test_post_bans_user(self):
        """POSTing to the ban_user_and_cleanup bans user for "spam" reason."""
        resp = self.client.post(self.ban_testuser_url)
        eq_(200, resp.status_code)

        testuser_banned = self.user_model.objects.get(username='testuser')
        ok_(not testuser_banned.is_active)

        bans = UserBan.objects.filter(user=self.testuser,
                                      by=self.admin,
                                      reason='Spam')
        ok_(bans.count())

    def test_post_banned_user(self):
        """POSTing to ban_user_and_cleanup for a banned user updates UserBan."""
        UserBan.objects.create(user=self.testuser, by=self.testuser2,
                               reason='Banned by unit test.',
                               is_active=True)

        resp = self.client.post(self.ban_testuser_url)
        eq_(200, resp.status_code)

        ok_(not self.testuser.is_active)

        bans = UserBan.objects.filter(user=self.testuser)

        # Assert that the ban exists, and 'by' and 'reason' fields are updated
        ok_(bans.count())
        eq_(bans.first().is_active, True)
        eq_(bans.first().by, self.admin)
        eq_(bans.first().reason, 'Spam')

    @override_config(AKISMET_KEY='dashboard')
    @requests_mock.mock()
    def test_post_submits_revisions_to_akismet_as_spam(self, mock_requests):
        """POSTing to ban_user_and_cleanup url submits revisions to akismet."""
        # Create 3 revisions for self.testuser, titled 'Revision 1', 'Revision 2'...
        num_revisions = 3
        revisions_created = self.create_revisions(
            num=num_revisions,
            document=self.document,
            creator=self.testuser)

        # Enable Akismet and mock calls to it
        Flag.objects.create(name=SPAM_SUBMISSIONS_FLAG, everyone=True)
        mock_requests.post(VERIFY_URL, content='valid')
        mock_requests.post(SPAM_URL, content=Akismet.submission_success)

        # The request
        data = {'revision-id': [rev.id for rev in revisions_created]}
        resp = self.client.post(self.ban_testuser_url, data=data)
        eq_(200, resp.status_code)

        # All of self.testuser's revisions have been submitted
        testuser_submissions = RevisionAkismetSubmission.objects.filter(revision__creator=self.testuser.id)
        eq_(testuser_submissions.count(), num_revisions)
        for submission in testuser_submissions:
            ok_(submission.revision in revisions_created)
        # No revisions submitted for self.testuser2, since self.testuser2 had no revisions
        testuser2_submissions = RevisionAkismetSubmission.objects.filter(revision__creator=self.testuser2.id)
        eq_(testuser2_submissions.count(), 0)
        # Akismet endpoints were called twice for each revision
        ok_(mock_requests.called)
        eq_(mock_requests.call_count, 2 * num_revisions)

    @override_config(AKISMET_KEY='dashboard')
    @requests_mock.mock()
    def test_post_submits_no_revisions_to_akismet_as_spam(self, mock_requests):
        """
        POSTing to ban_user_and_cleanup url does not submit to akismet.

        This occurs when: 1.) User has no revisions 2.) User's revisions were
        not in request.POST (not selected in the template)  3.) User being
        banned did not create the revisions being POSTed.
        """
        # Create 3 revisions for self.testuser, titled 'Revision 1', 'Revision 2'...
        num_revisions = 3
        revisions_created = self.create_revisions(
            num=num_revisions,
            document=self.document,
            creator=self.testuser)

        # Enable Akismet and mock calls to it
        Flag.objects.create(name=SPAM_SUBMISSIONS_FLAG, everyone=True)
        mock_requests.post(VERIFY_URL, content='valid')
        mock_requests.post(SPAM_URL, content=Akismet.submission_success)

        # Case 1.) User has no revisions
        data = {'revision-id': []}

        resp = self.client.post(self.ban_testuser2_url, data=data)
        eq_(200, resp.status_code)

        # No revisions submitted for self.testuser2, since self.testuser2 had no revisions
        testuser2_submissions = RevisionAkismetSubmission.objects.filter(
            revision__creator=self.testuser2.id)
        eq_(testuser2_submissions.count(), 0)
        # Akismet endpoints were not called
        eq_(mock_requests.call_count, 0)

        # Case 2.) User's revisions were not in request.POST (not selected in the template)
        data = {'revision-id': []}

        resp = self.client.post(self.ban_testuser_url, data=data)
        eq_(200, resp.status_code)

        # No revisions submitted for self.testuser, since no revisions were selected
        testuser_submissions = RevisionAkismetSubmission.objects.filter(
            revision__creator=self.testuser.id)
        eq_(testuser_submissions.count(), 0)
        # Akismet endpoints were not called
        eq_(mock_requests.call_count, 0)

        # Case 3.) User being banned did not create the revisions being POSTed
        data = {'revision-id': [rev.id for rev in revisions_created]}

        resp = self.client.post(self.ban_testuser2_url, data=data)
        eq_(200, resp.status_code)

        # No revisions submitted for self.testuser2, since revisions in the POST
        # were made by self.testuser
        testuser2_submissions = RevisionAkismetSubmission.objects.filter(
            revision__creator=self.testuser2.id)
        eq_(testuser2_submissions.count(), 0)
        # Akismet endpoints were not called
        eq_(mock_requests.call_count, 0)

#    TODO: Phase III:
#    def test_post_reverts_revisions(self):
#    def test_post_deletes_new_pages(self):
#
#    TODO: Phase IV:
#    def test_post_sends_email(self):


class UserViewsTest(UserTestCase):
    localizing_client = True

    def setUp(self):
        super(UserViewsTest, self).setUp()
        self.old_debug = settings.DEBUG
        settings.DEBUG = True
        self.client.logout()

    def tearDown(self):
        settings.DEBUG = self.old_debug

    def _get_current_form_field_values(self, doc):
        # Scrape out the existing significant form field values.
        fields = ('username', 'email', 'fullname', 'title', 'organization',
                  'location', 'irc_nickname', 'interests')
        form = dict()
        lookup_pattern = '#{prefix}edit *[name="{prefix}{field}"]'
        prefix = 'user-'
        for field in fields:
            lookup = lookup_pattern.format(prefix=prefix, field=field)
            form[prefix + field] = doc.find(lookup).val()
        form[prefix + 'country'] = 'us'
        form[prefix + 'format'] = 'html'
        return form

    def test_user_detail_view(self):
        """A user can be viewed"""
        testuser = self.user_model.objects.get(username='testuser')
        url = reverse('users.user_detail', args=(testuser.username,))
        response = self.client.get(url, follow=True)
        doc = pq(response.content)

        eq_(testuser.username,
            doc.find('#user-head.vcard .nickname').text())
        eq_(testuser.fullname,
            doc.find('#user-head.vcard .fn').text())
        eq_(testuser.title,
            doc.find('#user-head.vcard .title').text())
        eq_(testuser.organization,
            doc.find('#user-head.vcard .org').text())
        eq_(testuser.location,
            doc.find('#user-head.vcard .loc').text())
        eq_('IRC: ' + testuser.irc_nickname,
            doc.find('#user-head.vcard .irc').text())

    def test_my_user_page(self):
        u = self.user_model.objects.get(username='testuser')
        self.client.login(username=u.username, password=TESTUSER_PASSWORD)
        resp = self.client.get(reverse('users.my_detail_page'))
        eq_(302, resp.status_code)
        ok_(reverse('users.user_detail', args=(u.username,)) in
            resp['Location'])

    def test_bug_698971(self):
        """A non-numeric page number should not cause an error"""
        testuser = self.user_model.objects.get(username='testuser')

        url = '%s?page=asdf' % reverse('users.user_detail',
                                       args=(testuser.username,))

        try:
            self.client.get(url, follow=True)
        except PageNotAnInteger:
            self.fail("Non-numeric page number should not cause an error")

    def test_user_edit(self):
        testuser = self.user_model.objects.get(username='testuser')
        url = reverse('users.user_detail', args=(testuser.username,))
        response = self.client.get(url, follow=True)
        doc = pq(response.content)
        eq_(0, doc.find('#user-head .edit .button').length)

        self.client.login(username=testuser.username,
                          password=TESTUSER_PASSWORD)

        url = reverse('users.user_detail', args=(testuser.username,))
        response = self.client.get(url, follow=True)
        doc = pq(response.content)

        edit_button = doc.find('#user-head .user-buttons #edit-user')
        eq_(1, edit_button.length)

        url = edit_button.attr('href')
        response = self.client.get(url, follow=True)
        doc = pq(response.content)

        eq_(testuser.fullname,
            doc.find('#user-edit input[name="user-fullname"]').val())
        eq_(testuser.title,
            doc.find('#user-edit input[name="user-title"]').val())
        eq_(testuser.organization,
            doc.find('#user-edit input[name="user-organization"]').val())
        eq_(testuser.location,
            doc.find('#user-edit input[name="user-location"]').val())
        eq_(testuser.irc_nickname,
            doc.find('#user-edit input[name="user-irc_nickname"]').val())

        new_attrs = {
            'user-username': testuser.username,
            'user-email': 'testuser@test.com',
            'user-fullname': "Another Name",
            'user-title': "Another title",
            'user-organization': "Another org",
        }

        response = self.client.post(url, new_attrs, follow=True)
        doc = pq(response.content)

        eq_(1, doc.find('#user-head').length)
        eq_(new_attrs['user-fullname'],
            doc.find('#user-head .fn').text())
        eq_(new_attrs['user-title'],
            doc.find('#user-head .user-info .title').text())
        eq_(new_attrs['user-organization'],
            doc.find('#user-head .user-info .org').text())

        testuser = self.user_model.objects.get(username=testuser.username)
        eq_(new_attrs['user-fullname'], testuser.fullname)
        eq_(new_attrs['user-title'], testuser.title)
        eq_(new_attrs['user-organization'], testuser.organization)

    def test_my_user_edit(self):
        u = self.user_model.objects.get(username='testuser')
        self.client.login(username=u.username, password=TESTUSER_PASSWORD)
        resp = self.client.get(reverse('users.my_edit_page'))
        eq_(302, resp.status_code)
        ok_(reverse('users.user_edit', args=(u.username,)) in
            resp['Location'])

    def test_user_edit_beta(self):
        testuser = self.user_model.objects.get(username='testuser')
        self.client.login(username=testuser.username,
                          password=TESTUSER_PASSWORD)

        url = reverse('users.user_edit', args=(testuser.username,))
        response = self.client.get(url, follow=True)
        doc = pq(response.content)
        eq_(None, doc.find('input#id_user-beta').attr('checked'))

        form = self._get_current_form_field_values(doc)
        form['user-beta'] = True

        self.client.post(url, form, follow=True)

        url = reverse('users.user_edit', args=(testuser.username,))
        response = self.client.get(url, follow=True)
        doc = pq(response.content)
        eq_('checked', doc.find('input#id_user-beta').attr('checked'))

    def test_user_edit_websites(self):
        testuser = self.user_model.objects.get(username='testuser')
        self.client.login(username=testuser.username,
                          password=TESTUSER_PASSWORD)

        url = reverse('users.user_edit', args=(testuser.username,))
        response = self.client.get(url, follow=True)
        doc = pq(response.content)

        test_sites = {
            'twitter': 'http://twitter.com/lmorchard',
            'github': 'http://github.com/lmorchard',
            'stackoverflow': 'http://stackoverflow.com/users/lmorchard',
            'linkedin': 'https://www.linkedin.com/in/testuser',
            'mozillians': 'https://mozillians.org/u/testuser',
            'facebook': 'https://www.facebook.com/test.user'
        }

        form = self._get_current_form_field_values(doc)

        # Fill out the form with websites.
        form.update(dict(('user-%s_url' % k, v)
                         for k, v in test_sites.items()))

        # Submit the form, verify redirect to user detail
        response = self.client.post(url, form, follow=True)
        doc = pq(response.content)
        eq_(1, doc.find('#user-head').length)

        testuser = self.user_model.objects.get(pk=testuser.pk)

        # Verify the websites are saved in the user.
        for site, url in test_sites.items():
            url_attr_name = '%s_url' % site
            eq_(getattr(testuser, url_attr_name), url)

        # Verify the saved websites appear in the editing form
        url = reverse('users.user_edit', args=(testuser.username,))
        response = self.client.get(url, follow=True)
        doc = pq(response.content)
        for k, v in test_sites.items():
            eq_(v, doc.find('#user-edit *[name="user-%s_url"]' % k).val())

        # Come up with some bad sites, either invalid URL or bad URL prefix
        bad_sites = {
            'linkedin': 'HAHAHA WHAT IS A WEBSITE',
            'twitter': 'http://facebook.com/lmorchard',
            'stackoverflow': 'http://overqueueblah.com/users/lmorchard',
        }
        form.update(dict(('user-%s_url' % k, v)
                         for k, v in bad_sites.items()))

        # Submit the form, verify errors for all of the bad sites
        response = self.client.post(url, form, follow=True)
        doc = pq(response.content)
        eq_(1, doc.find('#user-edit').length)
        tmpl = '#user-edit #users .%s .errorlist'
        for n in ('linkedin', 'twitter', 'stackoverflow'):
            eq_(1, doc.find(tmpl % n).length)

    def test_user_edit_interests(self):
        testuser = self.user_model.objects.get(username='testuser')
        self.client.login(username=testuser.username,
                          password=TESTUSER_PASSWORD)

        url = reverse('users.user_edit', args=(testuser.username,))
        response = self.client.get(url, follow=True)
        doc = pq(response.content)

        test_tags = ['javascript', 'css', 'canvas', 'html', 'homebrewing']

        form = self._get_current_form_field_values(doc)

        form['user-interests'] = ', '.join(test_tags)

        response = self.client.post(url, form, follow=True)
        doc = pq(response.content)
        eq_(1, doc.find('#user-head').length)

        result_tags = [t.name.replace('profile:interest:', '')
                       for t in testuser.tags.all_ns('profile:interest:')]
        result_tags.sort()
        test_tags.sort()
        eq_(test_tags, result_tags)

        test_expertise = ['css', 'canvas']
        form['user-expertise'] = ', '.join(test_expertise)
        response = self.client.post(url, form, follow=True)
        doc = pq(response.content)

        eq_(1, doc.find('#user-head').length)

        result_tags = [t.name.replace('profile:expertise:', '')
                       for t in testuser.tags.all_ns('profile:expertise')]
        result_tags.sort()
        test_expertise.sort()
        eq_(test_expertise, result_tags)

        # Now, try some expertise tags not covered in interests
        test_expertise = ['css', 'canvas', 'mobile', 'movies']
        form['user-expertise'] = ', '.join(test_expertise)
        response = self.client.post(url, form, follow=True)
        doc = pq(response.content)

        eq_(1, doc.find('.error #id_user-expertise').length)

    def test_bug_709938_interests(self):
        testuser = self.user_model.objects.get(username='testuser')
        self.client.login(username=testuser.username,
                          password=TESTUSER_PASSWORD)

        url = reverse('users.user_edit', args=(testuser.username,))
        response = self.client.get(url, follow=True)
        doc = pq(response.content)

        test_tags = [u'science,Technology,paradox,knowledge,modeling,big data,'
                     u'vector,meme,heuristics,harmony,mathesis universalis,'
                     u'symmetry,mathematics,computer graphics,field,chemistry,'
                     u'religion,astronomy,physics,biology,literature,'
                     u'spirituality,Art,Philosophy,Psychology,Business,Music,'
                     u'Computer Science']

        form = self._get_current_form_field_values(doc)

        form['user-interests'] = test_tags

        response = self.client.post(url, form, follow=True)
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(1, doc.find('ul.errorlist li').length)
        assert ('Ensure this value has at most 255 characters'
                in doc.find('ul.errorlist li').text())

    def test_bug_698126_l10n(self):
        """Test that the form field names are localized"""
        testuser = self.user_model.objects.get(username='testuser')
        self.client.login(username=testuser.username,
                          password=TESTUSER_PASSWORD)

        url = reverse('users.user_edit', args=(testuser.username,))
        response = self.client.get(url, follow=True)
        for field in response.context['user_form'].fields:
            # if label is localized it's a lazy proxy object
            ok_(not isinstance(
                response.context['user_form'].fields[field].label, basestring),
                'Field %s is a string!' % field)


class Test404Case(UserTestCase):

    def test_404_logins(self):
        """The login buttons should display on the 404 page"""
        response = self.client.get('/something-doesnt-exist', follow=True)
        doc = pq(response.content)

        login_block = doc.find('.socialaccount-providers')
        ok_(len(login_block) > 0)
        eq_(404, response.status_code)

    def test_404_already_logged_in(self):
        """
        The login buttons should not display on the 404 page when the
        user is logged in
        """
        # View page as a logged in user
        self.client.login(username='testuser',
                          password='testpass')
        response = self.client.get('/something-doesnt-exist', follow=True)
        doc = pq(response.content)

        login_block = doc.find('.socialaccount-providers')
        eq_(len(login_block), 0)
        eq_(404, response.status_code)
        self.client.logout()


class AllauthPersonaTestCase(UserTestCase):
    """
    Test sign-up/in flow with Persona.
    """
    existing_persona_email = 'testuser@test.com'
    existing_persona_username = 'testuser'
    localizing_client = False

    def test_persona_auth_failure(self):
        """
        Failed Persona auth does not crash or otherwise error, but
        correctly redirects to an explanatory page.
        """
        with mock.patch('requests.post') as requests_mock:
            requests_mock.return_value.json.return_value = {
                'status': 'failure',
                'reason': 'this email address has been naughty'
            }
            response = self.client.post(reverse('persona_login'),
                                        follow=True)
            eq_(200, response.status_code)
            eq_(response.redirect_chain,
                [('http://testserver/users/persona/complete?process=&next=',
                  302)])

    def test_persona_auth_success(self):
        """
        Successful Persona auth of a new (i.e., no connected social
        account with that email) user redirects to the signup
        completion page.
        """
        with mock.patch('requests.post') as requests_mock:
            requests_mock.return_value.json.return_value = {
                'status': 'okay',
                'email': 'views_persona_auth@example.com',
            }
            response = self.client.post(reverse('persona_login'),
                                        follow=True)
            eq_(response.status_code, 200)
            expected_redirects = [
                ('http://testserver/users/persona/complete?process=&next=',
                 302),
                ('http://testserver/users/account/signup',
                 302),
            ]
            for red in expected_redirects:
                ok_(red in response.redirect_chain)

    def test_persona_signin(self):
        """
        When an existing user signs in with Persona, using the email
        address associated with their account, authentication is
        successful and redirects to the home page when no explicit
        'next' is provided.
        """
        with mock.patch('requests.post') as requests_mock:
            requests_mock.return_value.json.return_value = {
                'status': 'okay',
                'email': self.existing_persona_email,
            }
            response = self.client.post(reverse('persona_login'),
                                        follow=True)
            eq_(response.status_code, 200)
            expected_redirects = [
                ('http://testserver/users/persona/complete?process=&next=',
                 302),
                ('http://testserver/en-US/',
                 301)
            ]
            for red in expected_redirects:
                ok_(red in response.redirect_chain)

    def test_persona_signin_next(self):
        """
        When an existing user successfully authenticates with Persona,
        from a page which supplied a 'next' parameter, they are
        redirected back to that page following authentication.
        """
        with mock.patch('requests.post') as requests_mock:
            requests_mock.return_value.json.return_value = {
                'status': 'okay',
                'email': self.existing_persona_email,
            }
            doc_url = reverse('wiki.document', args=['article-title'],
                              locale=settings.WIKI_DEFAULT_LANGUAGE)
            response = self.client.post(reverse('persona_login'),
                                        data={'next': doc_url},
                                        follow=True)
            ok_(('http://testserver%s' % doc_url, 302) in response.redirect_chain)

    @override_config(RECAPTCHA_PRIVATE_KEY='private_key',
                     RECAPTCHA_PUBLIC_KEY='public_key')
    def test_persona_signin_captcha(self):
        persona_signup_email = 'views_persona_django_user@example.com'
        persona_signup_username = 'views_persona_django_user'

        with mock.patch('requests.post') as requests_mock:
            requests_mock.return_value.json.return_value = {
                'status': 'okay',
                'email': persona_signup_email,
            }
            self.client.post(reverse('persona_login'), follow=True)

        data = {'website': '',
                'username': persona_signup_username,
                'email': persona_signup_email,
                'terms': True,
                'g-recaptcha-response': 'FAILED'}
        signup_url = reverse('socialaccount_signup',
                             locale=settings.WIKI_DEFAULT_LANGUAGE)

        with mock.patch('captcha.client.request') as request_mock:
            request_mock.return_value.read.return_value = '{"success": null}'
            response = self.client.post(signup_url, data=data, follow=True)
        eq_(response.status_code, 200)
        eq_(response.context['form'].errors,
            {'captcha': [u'Incorrect, please try again.']})

    @mock.patch.dict(os.environ, {'RECAPTCHA_TESTING': 'True'})
    def test_persona_signup_create_django_user(self):
        """
        Signing up with Persona creates a new Django User instance.
        """
        persona_signup_email = 'views_persona_django_user@example.com'
        persona_signup_username = 'views_persona_django_user'

        with mock.patch('requests.post') as requests_mock:
            old_count = self.user_model.objects.count()
            requests_mock.return_value.json.return_value = {
                'status': 'okay',
                'email': persona_signup_email,
            }
            self.client.post(reverse('persona_login'), follow=True)
            data = {'website': '',
                    'username': persona_signup_username,
                    'email': persona_signup_email,
                    'terms': True,
                    'g-recaptcha-response': 'PASSED'}
            signup_url = reverse('socialaccount_signup',
                                 locale=settings.WIKI_DEFAULT_LANGUAGE)
            response = self.client.post(signup_url, data=data, follow=True)
            eq_(response.status_code, 200)
            # not on the signup page anymore
            ok_('form' not in response.context)

            # Did we get a new user?
            eq_(old_count + 1, self.user_model.objects.count())

            # Does it have the right attributes?
            testuser = None
            try:
                testuser = self.user_model.objects.order_by('-date_joined')[0]
            except IndexError:
                pass
            ok_(testuser)
            ok_(testuser.is_active)
            eq_(persona_signup_username, testuser.username)
            eq_(persona_signup_email, testuser.email)
            ok_(testuser.password.startswith(UNUSABLE_PASSWORD_PREFIX))

    @mock.patch.dict(os.environ, {'RECAPTCHA_TESTING': 'True'})
    def test_persona_signup_create_socialaccount(self):
        """
        Signing up with Persona creates a new SocialAccount instance.
        """
        persona_signup_email = 'views_persona_socialaccount@example.com'
        persona_signup_username = 'views_persona_socialaccount'

        with mock.patch('requests.post') as requests_mock:
            requests_mock.return_value.json.return_value = {
                'status': 'okay',
                'email': persona_signup_email,
            }
            self.client.post(reverse('persona_login'), follow=True)
            data = {'website': '',
                    'username': persona_signup_username,
                    'email': persona_signup_email,
                    'terms': True,
                    'g-recaptcha-response': 'PASSED'}
            signup_url = reverse('socialaccount_signup',
                                 locale=settings.WIKI_DEFAULT_LANGUAGE)
            self.client.post(signup_url, data=data, follow=True)
            try:
                socialaccount = (SocialAccount.objects
                                              .filter(user__username=persona_signup_username))[0]
            except IndexError:
                socialaccount = None
            ok_(socialaccount is not None)
            eq_('persona', socialaccount.provider)
            eq_(persona_signup_email, socialaccount.uid)
            eq_({'status': 'okay', 'email': persona_signup_email},
                socialaccount.extra_data)
            testuser = self.user_model.objects.get(username=persona_signup_username)
            eq_(testuser.id, socialaccount.user.id)


class KumaGitHubTests(UserTestCase):
    localizing_client = False
    mocked_user_response = """
        {
            "login": "%(username)s",
            "id": 1,
            "avatar_url": "https://github.com/images/error/octocat_happy.gif",
            "gravatar_id": "somehexcode",
            "url": "https://api.github.com/users/octocat",
            "html_url": "https://github.com/octocat",
            "followers_url": "https://api.github.com/users/octocat/followers",
            "following_url": "https://api.github.com/users/octocat/following{/other_user}",
            "gists_url": "https://api.github.com/users/octocat/gists{/gist_id}",
            "starred_url": "https://api.github.com/users/octocat/starred{/owner}{/repo}",
            "subscriptions_url": "https://api.github.com/users/octocat/subscriptions",
            "organizations_url": "https://api.github.com/users/octocat/orgs",
            "repos_url": "https://api.github.com/users/octocat/repos",
            "events_url": "https://api.github.com/users/octocat/events{/privacy}",
            "received_events_url": "https://api.github.com/users/octocat/received_events",
            "type": "User",
            "site_admin": false,
            "name": "monalisa octocat",
            "company": "GitHub",
            "blog": "https://github.com/blog",
            "location": "San Francisco",
            "email": %(public_email)s,
            "hireable": false,
            "public_repos": 2,
            "public_gists": 1,
            "followers": 20,
            "following": 0,
            "created_at": "2008-01-14T04:33:35Z",
            "updated_at": "2008-01-14T04:33:35Z"
        }"""
    mocked_email_response = """
        [
            {
                "email": "%(verified_email)s",
                "verified": true,
                "primary": true
            }
        ]"""

    def get_login_response_json(self, with_refresh_token=True):
        rt = ''
        if with_refresh_token:
            rt = ',"refresh_token": "testrf"'
        return """{
            "uid":"weibo",
            "access_token":"testac"
            %s }""" % rt

    def setUp(self):
        self.signup_url = reverse('socialaccount_signup',
                                  locale=settings.WIKI_DEFAULT_LANGUAGE)
        self.provider = registry.by_id(KumaGitHubProvider.id)
        app = SocialApp.objects.create(provider=self.provider.id,
                                       name=self.provider.id,
                                       client_id='app123id',
                                       key=self.provider.id,
                                       secret='dummy')
        app.sites.add(Site.objects.get_current())

    def test_login(self):
        resp = self.login()
        self.assertRedirects(resp, self.signup_url)

    def test_matching_user(self):
        self.login()
        response = self.client.get(self.signup_url)
        self.assertTrue('matching_user' in response.context)
        self.assertEqual(response.context['matching_user'], None)
        octocat = user(username='octocat', save=True)
        response = self.client.get(self.signup_url)
        self.assertEqual(response.context['matching_user'], octocat)

    @mock.patch.dict(os.environ, {'RECAPTCHA_TESTING': 'True'})
    def test_email_addresses(self):
        self.login(username='octocat2')
        response = self.client.get(self.signup_url)
        email_address = response.context['email_addresses']

        # first check if the public email address has been found
        self.assertTrue('octocat@github.com' in email_address)
        self.assertEqual(email_address['octocat@github.com'],
                         {'verified': False,
                          'email': 'octocat@github.com',
                          'primary': False})
        # then check if the private and verified-at-GitHub email address
        # has been found
        self.assertTrue('octo.cat@github-inc.com' in email_address)
        self.assertEqual(email_address['octo.cat@github-inc.com'],
                         {'verified': True,
                          'email': 'octo.cat@github-inc.com',
                          'primary': True})
        # then check if the radio button's default value is the public email
        # address
        self.assertEqual(response.context['form'].initial['email'],
                         'octocat@github.com')

        unverified_email = 'o.ctocat@gmail.com'
        data = {
            'website': '',
            'username': 'octocat',
            'email': SignupForm.other_email_value,  # = use other_email
            'other_email': unverified_email,
            'terms': True,
            'g-recaptcha-response': 'PASSED',
        }
        self.assertFalse((EmailAddress.objects.filter(email=unverified_email)
                                              .exists()))
        response = self.client.post(self.signup_url, data=data, follow=True)
        unverified_email_addresses = EmailAddress.objects.filter(
            email=unverified_email)
        self.assertTrue(unverified_email_addresses.exists())
        self.assertEquals(unverified_email_addresses.count(), 1)
        self.assertTrue(unverified_email_addresses[0].primary)
        self.assertFalse(unverified_email_addresses[0].verified)

    def test_email_addresses_with_no_public(self):
        self.login(username='private_octocat',
                   verified_email='octocat@github.com',
                   public_email=None)
        response = self.client.get(self.signup_url)
        self.assertEqual(response.context["form"].initial["email"], 'octocat@github.com')

    def test_matching_accounts(self):
        testemail = 'octo.cat.III@github-inc.com'
        self.login(username='octocat3', verified_email=testemail)
        response = self.client.get(self.signup_url)
        self.assertEqual(list(response.context['matching_accounts']),
                         [])
        # assuming there is already a Persona account with the given email
        # address
        octocat3 = user(username='octocat3', is_active=True,
                        email=testemail, password='test', save=True)
        social_account = SocialAccount.objects.create(uid=testemail,
                                                      provider='persona',
                                                      user=octocat3)
        response = self.client.get(self.signup_url)
        self.assertTrue(response.context['matching_accounts'],
                        [social_account])

    def test_account_tokens(self, multiple_login=False):
        testemail = 'account_token@acme.com'
        testuser = user(username='user', is_active=True,
                        email=testemail, password='test', save=True)
        email(user=testuser, email=testemail,
              primary=True, verified=True, save=True)
        self.client.login(username=testuser.username,
                          password='test')
        self.login(process='connect')
        if multiple_login:
            self.login(with_refresh_token=False, process='connect')
        # get account
        social_account = SocialAccount.objects.get(user=testuser,
                                                   provider=self.provider.id)
        # get token
        social_token = social_account.socialtoken_set.get()
        # verify access_token and refresh_token
        self.assertEqual('testac', social_token.token)
        self.assertEqual(social_token.token_secret,
                         json.loads(self.get_login_response_json(
                             with_refresh_token=True)).get(
                                 'refresh_token', ''))

    def test_account_refresh_token_saved_next_login(self):
        """
        fails if a login missing a refresh token, deletes the previously
        saved refresh token. Systems such as google's oauth only send
        a refresh token on first login.
        """
        self.test_account_tokens(multiple_login=True)

    def login(self,
              username='octocat',
              verified_email='octo.cat@github-inc.com',
              process='login', with_refresh_token=True,
              public_email='octocat@github.com'):
        resp = self.client.get(reverse('github_login',
                                       locale=settings.WIKI_DEFAULT_LANGUAGE),
                               {'process': process})
        path = urlparse(resp['location'])
        query = parse_qs(path.query)
        complete_url = reverse('github_callback', unprefixed=True)
        self.assertGreater(query['redirect_uri'][0]
                           .find(complete_url), 0)
        response_json = self.get_login_response_json(
            with_refresh_token=with_refresh_token)
        with mocked_response(
            MockedResponse(200, response_json,
                           {'content-type': 'application/json'}),
                MockedResponse(200,
                               self.mocked_user_response %
                               {'username': username,
                                'public_email': json.dumps(public_email)}),
                MockedResponse(200,
                               self.mocked_email_response %
                               {'verified_email': verified_email})):
            resp = self.client.get(complete_url,
                                   {'code': 'test',
                                    'state': query['state'][0]},
                                   follow=True)
        return resp
