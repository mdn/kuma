from nose.tools import eq_, ok_
from pyquery import PyQuery as pq

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase

from kuma.core.urlresolvers import reverse
from kuma.users.tests import user

from ..models import Key
from ..views import ITEMS_PER_PAGE


class RefetchingUserTestCase(TestCase):

    def _cache_bust_user_perms(self):
        # method to cache-bust the user perms by re-fetching from DB
        # https://docs.djangoproject.com/en/1.7/topics/auth/default/#permissions-and-authorization
        self.user = get_user_model().objects.get(username=self.user.username)


class KeyViewsTest(RefetchingUserTestCase):

    def setUp(self):
        username = 'tester23'
        password = 'trustno1'
        email = 'tester23@example.com'

        self.user = user(username=username, email=email,
                         password=password, save=True)
        self.client.login(username=username, password=password)

        # Give self.user (tester23) keys permissions
        add_perm = Permission.objects.get(codename='add_key')
        del_perm = Permission.objects.get(codename='delete_key')
        self.user.user_permissions.add(add_perm)
        self.user.user_permissions.add(del_perm)

        self._cache_bust_user_perms()

        username2 = 'someone'
        password2 = 'somepass'
        email2 = 'someone@example.com'

        self.user2 = user(username=username2, email=email2,
                          password=password2, save=True)

        self.key1 = Key(user=self.user, description='Test Key 1')
        self.key1.save()
        self.key2 = Key(user=self.user, description='Test Key 2')
        self.key2.save()
        self.key3 = Key(user=self.user2, description='Test Key 3')
        self.key3.save()

    def test_new_key(self):
        data = {"description": "This is meant for a test app"}
        url = reverse('authkeys.new', locale='en-US')

        # Check out the creation page, look for the form.
        resp = self.client.get(url)
        eq_(200, resp.status_code)
        page = pq(resp.content)
        eq_(1, page.find('form.key').length)

        # We don't have this key yet, right?
        keys = Key.objects.filter(description=data['description'])
        eq_(0, keys.count())

        # Okay, create it.
        resp = self.client.post(url, data, follow=False)
        eq_(200, resp.status_code)

        # We have the key now, right?
        keys = Key.objects.filter(description=data['description'])
        eq_(1, keys.count())

        # Okay, and it should belong to the logged-in user
        key = keys[0]
        eq_(key.user, self.user)

        # Take a look at the description and key shown on the result page.
        page = pq(resp.content)
        ok_(data['description'], page.find('.key .description').text())
        ok_(key.key, page.find('.key .key').text())

        # Ensure the secret on the page checks out.
        secret = page.find('.key .secret').text()
        ok_(key.check_secret(secret))

    def test_list_key(self):
        """The current user's keys should be shown, but only that user's"""
        url = reverse('authkeys.list', locale='en-US')
        resp = self.client.get(url)
        eq_(200, resp.status_code)
        page = pq(resp.content)

        for ct, key in ((1, self.key1), (1, self.key2), (0, self.key3)):
            key_row = page.find('.option-list #key-%s' % key.pk)
            eq_(ct, key_row.length)
            if ct > 0:
                eq_(key.description, key_row.find('.description').text())

    def test_key_history(self):
        # Assemble some sample log lines
        log_lines = []
        for i in range(0, ITEMS_PER_PAGE * 2):
            log_lines.append(('ping', self.user2, 'Number #%s' % i))

        # Record the log lines for this key
        for l in log_lines:
            self.key1.log(*l)

        # Reverse the lines for comparison.
        log_lines.reverse()

        # Iterate through 2 expected pages...
        for qs, offset in (('', 0), ('?page=2', ITEMS_PER_PAGE)):
            url = '%s%s' % (reverse('authkeys.history', args=(self.key1.pk,),
                                    locale='en-US'), qs)
            resp = self.client.get(url)
            eq_(200, resp.status_code)
            page = pq(resp.content)

            rows = page.find('.item')
            for idx in range(0, ITEMS_PER_PAGE):
                row = rows.eq(idx)
                expected = log_lines[idx + offset]
                line = (row.find('.action').text(),
                        row.find('.object').text(),
                        row.find('.notes').text())
                eq_(expected[0], line[0])
                ok_('%s' % expected[1] in line[1])
                eq_(expected[2], line[2])

    def test_delete_key(self):
        """User should be able to delete own keys, but no one else's"""
        url = reverse('authkeys.delete', args=(self.key3.pk,),
                      locale='en-US')
        resp = self.client.get(url, follow=True)
        eq_(403, resp.status_code)

        resp = self.client.post(url, follow=False)
        ok_(403, resp.status_code)

        url = reverse('authkeys.delete', args=(self.key1.pk,),
                      locale='en-US')
        resp = self.client.get(url, follow=True)
        eq_(200, resp.status_code)

        page = pq(resp.content)
        eq_(self.key1.description, page.find('.description').text())

        resp = self.client.post(url, follow=False)
        ok_(302, resp.status_code)

        eq_(0, Key.objects.filter(pk=self.key1.pk).count())


class KeyViewsPermissionTest(RefetchingUserTestCase):

    def setUp(self):
        username = 'tester23'
        password = 'trustno1'
        email = 'tester23@example.com'

        self.user = user(username=username, email=email,
                         password=password, save=True)
        self.client.login(username=username, password=password)

    def test_new_key_requires_permission(self):
        url = reverse('authkeys.new', locale='en-US')
        resp = self.client.get(url)
        eq_(403, resp.status_code)

        perm = Permission.objects.get(codename='add_key')
        self.user.user_permissions.add(perm)
        self._cache_bust_user_perms()

        resp = self.client.get(url)
        eq_(200, resp.status_code)

    def test_delete_key_requires_separate_permission(self):
        self.key1 = Key(user=self.user, description='Test Key 1')
        self.key1.save()

        url = reverse('authkeys.delete', locale='en-US', args=(self.key1.pk,))
        resp = self.client.get(url)
        eq_(403, resp.status_code)
        self._cache_bust_user_perms()

        resp = self.client.get(url)
        eq_(403, resp.status_code)

        perm = Permission.objects.get(codename='delete_key')
        self.user.user_permissions.add(perm)
        self._cache_bust_user_perms()

        resp = self.client.get(url)
        eq_(200, resp.status_code)
