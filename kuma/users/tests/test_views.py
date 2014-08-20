import logging

from django.conf import settings
from django.contrib.auth.models import User
from django.core.paginator import PageNotAnInteger

import mock
from nose.tools import eq_, ok_
from nose.plugins.attrib import attr
from pyquery import PyQuery as pq

from devmo.tests import mock_lookup_user, LocalizingClient
from sumo.tests import TestCase
from sumo.urlresolvers import reverse

from ..models import UserProfile, UserBan

TESTUSER_PASSWORD = 'testpass'


class OldProfileTestCase(TestCase):
    fixtures = ['test_users.json']

    def test_old_profile_url_gone(self):
        response = self.client.get('/users/edit', follow=True)
        eq_(404, response.status_code)


class BanTestCase(TestCase):
    fixtures = ['test_users.json']

    @attr('bans')
    def test_ban_permission(self):
        """The ban permission controls access to the ban view."""
        client = LocalizingClient()
        admin = User.objects.get(username='admin')
        testuser = User.objects.get(username='testuser')

        # testuser doesn't have ban permission, can't ban.
        client.login(username='testuser',
                     password='testpass')
        ban_url = reverse('users.ban_user',
                          kwargs={'user_id': admin.id})
        resp = client.get(ban_url)
        eq_(302, resp.status_code)
        ok_(str(settings.LOGIN_URL) in resp['Location'])
        client.logout()

        # admin has ban permission, can ban.
        client.login(username='admin',
                     password='testpass')
        ban_url = reverse('users.ban_user',
                          kwargs={'user_id': testuser.id})
        resp = client.get(ban_url)
        eq_(200, resp.status_code)

    @attr('bans')
    def test_ban_view(self):
        testuser = User.objects.get(username='testuser')
        admin = User.objects.get(username='admin')

        client = LocalizingClient()
        client.login(username='admin', password='testpass')

        data = {'reason': 'Banned by unit test.'}
        ban_url = reverse('users.ban_user',
                          kwargs={'user_id': testuser.id})

        resp = client.post(ban_url, data)
        eq_(302, resp.status_code)
        ok_(testuser.get_absolute_url() in resp['Location'])

        testuser_banned = User.objects.get(username='testuser')
        ok_(not testuser_banned.is_active)

        bans = UserBan.objects.filter(user=testuser,
                                      by=admin,
                                      reason='Banned by unit test.')
        ok_(bans.count())

    @attr('bans')
    def test_bug_811751_banned_profile(self):
        """A banned user's profile should not be viewable"""
        user = User.objects.get(username='testuser')
        url = reverse('users.profile', args=(user.username,))

        # Profile viewable if not banned
        response = self.client.get(url, follow=True)
        self.assertNotEqual(response.status_code, 403)

        # Ban User
        admin = User.objects.get(username='admin')
        testuser = User.objects.get(username='testuser')
        ban = UserBan(user=testuser, by=admin,
                      reason='Banned by unit test.',
                      is_active=True)
        ban.save()

        # Profile not viewable if banned
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 403)

        # Admin can view banned user's profile
        self.client.login(username='admin', password='testpass')
        response = self.client.get(url, follow=True)
        self.assertNotEqual(response.status_code, 403)


class ProfileViewsTest(TestCase):
    fixtures = ['test_users.json']

    def setUp(self):
        self.old_debug = settings.DEBUG
        settings.DEBUG = True
        self.client = LocalizingClient()
        self.client.logout()

    def tearDown(self):
        settings.DEBUG = self.old_debug

    def _get_current_form_field_values(self, doc):
        # Scrape out the existing significant form field values.
        form = dict()
        for fn in ('email', 'fullname', 'title', 'organization', 'location',
                   'irc_nickname', 'bio', 'interests'):
            form[fn] = doc.find('#profile-edit *[name="profile-%s"]' % fn).val()
        form['country'] = 'us'
        form['format'] = 'html'
        return form

    @attr('docs_activity')
    def test_profile_view(self):
        """A user profile can be viewed"""
        profile = UserProfile.objects.get(user__username='testuser')
        user = profile.user
        url = reverse('users.profile', args=(user.username,))
        r = self.client.get(url, follow=True)
        doc = pq(r.content)

        eq_(profile.user.username,
            doc.find('#profile-head.vcard .nickname').text())
        eq_(profile.fullname,
            doc.find('#profile-head.vcard .fn').text())
        eq_(profile.title,
            doc.find('#profile-head.vcard .title').text())
        eq_(profile.organization,
            doc.find('#profile-head.vcard .org').text())
        eq_(profile.location,
            doc.find('#profile-head.vcard .loc').text())
        eq_('IRC: ' + profile.irc_nickname,
            doc.find('#profile-head.vcard .irc').text())
        eq_(profile.bio,
            doc.find('#profile-head.vcard .bio').text())

    def test_my_profile_view(self):
        u = User.objects.get(username='testuser')
        self.client.login(username=u.username, password=TESTUSER_PASSWORD)
        resp = self.client.get(reverse('users.my_profile'))
        eq_(302, resp.status_code)
        ok_(reverse('users.profile', args=(u.username,)) in
            resp['Location'])

    def test_bug_698971(self):
        """A non-numeric page number should not cause an error"""
        user = User.objects.get(username='testuser')

        url = '%s?page=asdf' % reverse('users.profile', args=(user.username,))

        try:
            self.client.get(url, follow=True)
        except PageNotAnInteger:
            ok_(False, "Non-numeric page number should not cause an error")

    @mock.patch('basket.lookup_user')
    @mock.patch('basket.subscribe')
    @mock.patch('basket.unsubscribe')
    def test_profile_edit(self, unsubscribe, subscribe, lookup_user):
        lookup_user.return_value = mock_lookup_user()
        subscribe.return_value = True
        unsubscribe.return_value = True
        profile = UserProfile.objects.get(user__username='testuser')
        user = profile.user
        url = reverse('users.profile', args=(user.username,))
        r = self.client.get(url, follow=True)
        doc = pq(r.content)
        eq_(0, doc.find('#profile-head .edit .button').length)

        self.client.login(username=user.username,
                password=TESTUSER_PASSWORD)

        url = reverse('users.profile', args=(user.username,))
        r = self.client.get(url, follow=True)
        doc = pq(r.content)

        edit_button = doc.find('#profile-head .edit #edit-profile')
        eq_(1, edit_button.length)

        url = edit_button.attr('href')
        r = self.client.get(url, follow=True)
        doc = pq(r.content)

        eq_(profile.fullname,
            doc.find('#profile-edit input[name="profile-fullname"]').val())
        eq_(profile.title,
            doc.find('#profile-edit input[name="profile-title"]').val())
        eq_(profile.organization,
            doc.find('#profile-edit input[name="profile-organization"]').val())
        eq_(profile.location,
            doc.find('#profile-edit input[name="profile-location"]').val())
        eq_(profile.irc_nickname,
            doc.find('#profile-edit input[name="profile-irc_nickname"]').val())

        new_attrs = {
            'profile-email': 'testuser@test.com',
            'profile-fullname': "Another Name",
            'profile-title': "Another title",
            'profile-organization': "Another org",
            'profile-country': "us",
            'profile-format': "html"
        }

        r = self.client.post(url, new_attrs, follow=True)
        doc = pq(r.content)

        eq_(1, doc.find('#profile-head').length)
        eq_(new_attrs['profile-fullname'],
            doc.find('#profile-head .main .fn').text())
        eq_(new_attrs['profile-title'],
            doc.find('#profile-head .info .title').text())
        eq_(new_attrs['profile-organization'],
            doc.find('#profile-head .info .org').text())

        profile = UserProfile.objects.get(user__username=user.username)
        eq_(new_attrs['profile-fullname'], profile.fullname)
        eq_(new_attrs['profile-title'], profile.title)
        eq_(new_attrs['profile-organization'], profile.organization)

    def test_my_profile_edit(self):
        u = User.objects.get(username='testuser')
        self.client.login(username=u.username, password=TESTUSER_PASSWORD)
        resp = self.client.get(reverse('users.my_profile_edit'))
        eq_(302, resp.status_code)
        ok_(reverse('users.profile_edit', args=(u.username,)) in
            resp['Location'])

    @mock.patch('basket.lookup_user')
    @mock.patch('basket.subscribe')
    @mock.patch('basket.unsubscribe')
    def test_profile_edit_beta(self, unsubscribe, subscribe, lookup_user):
        lookup_user.return_value = mock_lookup_user()
        subscribe.return_value = True
        unsubscribe.return_value = True
        user = User.objects.get(username='testuser')
        self.client.login(username=user.username,
                          password=TESTUSER_PASSWORD)

        url = reverse('users.profile_edit',
                      args=(user.username,))
        r = self.client.get(url, follow=True)
        doc = pq(r.content)
        eq_(None, doc.find('input#id_profile-beta').attr('checked'))

        form = self._get_current_form_field_values(doc)
        form['profile-beta'] = True

        r = self.client.post(url, form, follow=True)

        url = reverse('users.profile_edit',
                      args=(user.username,))
        r = self.client.get(url, follow=True)
        doc = pq(r.content)
        eq_('checked', doc.find('input#id_profile-beta').attr('checked'))

    @mock.patch('basket.lookup_user')
    @mock.patch('basket.subscribe')
    @mock.patch('basket.unsubscribe')
    def test_profile_edit_websites(self, unsubscribe, subscribe, lookup_user):
        lookup_user.return_value = mock_lookup_user()
        subscribe.return_value = True
        unsubscribe.return_value = True

        user = User.objects.get(username='testuser')
        self.client.login(username=user.username,
                password=TESTUSER_PASSWORD)

        url = reverse('users.profile_edit',
                      args=(user.username,))
        r = self.client.get(url, follow=True)
        doc = pq(r.content)

        test_sites = {
            u'website': u'http://example.com/',
            u'twitter': u'http://twitter.com/lmorchard',
            u'github': u'http://github.com/lmorchard',
            u'stackoverflow': u'http://stackoverflow.com/users/lmorchard',
            u'linkedin': u'https://www.linkedin.com/in/testuser',
            u'mozillians': u'https://mozillians.org/u/testuser',
            u'facebook': u'https://www.facebook.com/test.user'
        }

        form = self._get_current_form_field_values(doc)

        # Fill out the form with websites.
        form.update(dict(('profile-websites_%s' % k, v)
                    for k, v in test_sites.items()))

        # Submit the form, verify redirect to profile detail
        r = self.client.post(url, form, follow=True)
        doc = pq(r.content)
        eq_(1, doc.find('#profile-head').length)

        p = UserProfile.objects.get(user=user)

        # Verify the websites are saved in the profile.
        eq_(test_sites, p.websites)

        # Verify the saved websites appear in the editing form
        url = reverse('users.profile_edit',
                      args=(user.username,))
        r = self.client.get(url, follow=True)
        doc = pq(r.content)
        for k, v in test_sites.items():
            eq_(v, doc.find('#profile-edit *[name="profile-websites_%s"]' % k).val())

        # Come up with some bad sites, either invalid URL or bad URL prefix
        bad_sites = {
            u'website': u'HAHAHA WHAT IS A WEBSITE',
            u'twitter': u'http://facebook.com/lmorchard',
            u'stackoverflow': u'http://overqueueblah.com/users/lmorchard',
        }
        form.update(dict(('profile-websites_%s' % k, v)
                    for k, v in bad_sites.items()))

        # Submit the form, verify errors for all of the bad sites
        r = self.client.post(url, form, follow=True)
        doc = pq(r.content)
        eq_(1, doc.find('#profile-edit').length)
        tmpl = '#profile-edit #profiles .%s .errorlist'
        for n in ('website', 'twitter', 'stackoverflow'):
            eq_(1, doc.find(tmpl % n).length)

    @mock.patch('basket.lookup_user')
    @mock.patch('basket.subscribe')
    @mock.patch('basket.unsubscribe')
    def test_profile_edit_interests(self,
                                    unsubscribe,
                                    subscribe,
                                    lookup_user):
        lookup_user.return_value = mock_lookup_user()
        subscribe.return_value = True
        unsubscribe.return_value = True

        user = User.objects.get(username='testuser')
        self.client.login(username=user.username,
                password=TESTUSER_PASSWORD)

        url = reverse('users.profile_edit',
                      args=(user.username,))
        r = self.client.get(url, follow=True)
        doc = pq(r.content)

        test_tags = ['javascript', 'css', 'canvas', 'html', 'homebrewing']

        form = self._get_current_form_field_values(doc)

        form['profile-interests'] = ', '.join(test_tags)

        r = self.client.post(url, form, follow=True)
        doc = pq(r.content)
        eq_(1, doc.find('#profile-head').length)

        p = UserProfile.objects.get(user=user)

        result_tags = [t.name.replace('profile:interest:', '')
                for t in p.tags.all_ns('profile:interest:')]
        result_tags.sort()
        test_tags.sort()
        eq_(test_tags, result_tags)

        test_expertise = ['css', 'canvas']
        form['profile-expertise'] = ', '.join(test_expertise)
        r = self.client.post(url, form, follow=True)
        doc = pq(r.content)

        eq_(1, doc.find('#profile-head').length)

        p = UserProfile.objects.get(user=user)

        result_tags = [t.name.replace('profile:expertise:', '')
                for t in p.tags.all_ns('profile:expertise')]
        result_tags.sort()
        test_expertise.sort()
        eq_(test_expertise, result_tags)

        # Now, try some expertise tags not covered in interests
        test_expertise = ['css', 'canvas', 'mobile', 'movies']
        form['profile-expertise'] = ', '.join(test_expertise)
        r = self.client.post(url, form, follow=True)
        doc = pq(r.content)

        eq_(1, doc.find('.error #id_profile-expertise').length)

    @mock.patch('basket.lookup_user')
    @mock.patch('basket.subscribe')
    @mock.patch('basket.unsubscribe')
    def test_bug_709938_interests(self, unsubscribe, subscribe, lookup_user):
        lookup_user.return_value = mock_lookup_user()
        subscribe.return_value = True
        unsubscribe.return_value = True
        user = User.objects.get(username='testuser')
        self.client.login(username=user.username, password=TESTUSER_PASSWORD)

        url = reverse('users.profile_edit', args=(user.username,))
        r = self.client.get(url, follow=True)
        doc = pq(r.content)

        test_tags = [u'science,Technology,paradox,knowledge,modeling,big data,'
                     u'vector,meme,heuristics,harmony,mathesis universalis,'
                     u'symmetry,mathematics,computer graphics,field,chemistry,'
                     u'religion,astronomy,physics,biology,literature,'
                     u'spirituality,Art,Philosophy,Psychology,Business,Music,'
                     u'Computer Science']

        form = self._get_current_form_field_values(doc)

        form['profile-interests'] = test_tags

        r = self.client.post(url, form, follow=True)
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_(1, doc.find('ul.errorlist li').length)
        assert ('Ensure this value has at most 255 characters'
                in doc.find('ul.errorlist li').text())

    @mock.patch('basket.lookup_user')
    @mock.patch('basket.subscribe')
    @mock.patch('basket.unsubscribe')
    def test_bug_698126_l10n(self, unsubscribe, subscribe, lookup_user):
        """Test that the form field names are localized"""
        lookup_user.return_value = mock_lookup_user()
        subscribe.return_value = True
        unsubscribe.return_value = True
        user = User.objects.get(username='testuser')
        self.client.login(username=user.username,
            password=TESTUSER_PASSWORD)

        url = reverse('users.profile_edit',
            args=(user.username,))
        r = self.client.get(url, follow=True)
        for field in r.context['profile_form'].fields:
            # if label is localized it's a lazy proxy object
            ok_(not isinstance(
                r.context['profile_form'].fields[field].label, basestring),
                'Field %s is a string!' % field)


class SignInTestCase(TestCase):
    fixtures = ['test_users.json', 'wiki/documents.json']

    def test_allauth_signin_returns_to_doc(self):
        """When signing in from a doc, return straight to the doc."""
        url = reverse('wiki.document', args=['article-title'],
                      locale=settings.WIKI_DEFAULT_LANGUAGE)
        response = self.client.get(url)
        # splitting the href string on the - character beceause allauth seems
        # to mangle it
        href_start = "javascript:allauth.persona.login('/en"
        href_mid = "US/docs/article"
        href_end = "title', 'login')"
        ok_(href_start in unicode(response.content, 'utf-8'))
        ok_(href_mid in unicode(response.content, 'utf-8'))
        ok_(href_end in unicode(response.content, 'utf-8'))


class Test404Case(TestCase):
    fixtures = ['test_users.json']

    def test_404_logins(self):
        """The login buttons should display on the 404 page"""
        response = self.client.get('/something-doesnt-exist', follow=True)
        doc = pq(response.content)

        login_block = doc.find('.socialaccount_providers')
        ok_(len(login_block) > 0)
        eq_(404, response.status_code)

    def test_404_already_logged_in(self):
        """The login buttons should not display on the 404 page when the user is logged in"""
        client = LocalizingClient()

        # View page as a logged in user
        client.login(username='testuser',
                     password='testpass')
        response = client.get('/something-doesnt-exist', follow=True)
        doc = pq(response.content)

        login_block = doc.find('.socialaccount_providers')
        eq_(len(login_block), 0)
        eq_(404, response.status_code)
        client.logout()
