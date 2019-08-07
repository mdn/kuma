from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from pyquery import PyQuery as pq
import pytest

from kuma.core.tests import assert_no_cache_header, assert_redirect_to_wiki

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
        url = reverse('authkeys.new')

        # Check out the creation page, look for the form.
        resp = self.client.get(url, HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 200
        assert_no_cache_header(resp)
        page = pq(resp.content)
        assert page.find('form.key').length == 1

        # We don't have this key yet, right?
        keys = Key.objects.filter(description=data['description'])
        assert keys.count() == 0

        # Okay, create it.
        resp = self.client.post(url, data, follow=False,
                                HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 200
        assert_no_cache_header(resp)

        # We have the key now, right?
        keys = Key.objects.filter(description=data['description'])
        assert keys.count() == 1

        # Okay, and it should belong to the logged-in user
        key = keys[0]
        assert key.user == self.user

        # Take a look at the description and key shown on the result page.
        page = pq(resp.content)
        assert page.find('.key .description').text() == data['description']
        assert page.find('.key .key').text() == key.key

        # Ensure the secret on the page checks out.
        secret = page.find('.key .secret').text()
        assert key.check_secret(secret)

    def test_list_key(self):
        """The current user's keys should be shown, but only that user's"""
        url = reverse('authkeys.list')
        resp = self.client.get(url, HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 200
        assert_no_cache_header(resp)
        page = pq(resp.content)

        for ct, key in ((1, self.key1), (1, self.key2), (0, self.key3)):
            key_row = page.find('.option-list #key-%s' % key.pk)
            assert key_row.length == ct
            if ct > 0:
                assert key_row.find('.description').text() == key.description

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
            url = '%s%s' % (reverse('authkeys.history', args=(self.key1.pk,)),
                            qs)
            resp = self.client.get(url, HTTP_HOST=settings.WIKI_HOST)
            assert resp.status_code == 200
            assert_no_cache_header(resp)
            page = pq(resp.content)

            rows = page.find('.item')
            for idx in range(0, ITEMS_PER_PAGE):
                row = rows.eq(idx)
                expected = log_lines[idx + offset]
                line = (row.find('.action').text(),
                        row.find('.object').text(),
                        row.find('.notes').text())
                assert line[0] == expected[0]
                assert ('%s' % expected[1]) in line[1]
                assert line[2] == expected[2]

    def test_delete_key(self):
        """User should be able to delete own keys, but no one else's"""
        url = reverse('authkeys.delete', args=(self.key3.pk,))
        resp = self.client.get(url, HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 403
        assert_no_cache_header(resp)

        resp = self.client.post(url, follow=False, HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 403
        assert_no_cache_header(resp)

        url = reverse('authkeys.delete', args=(self.key1.pk,))
        resp = self.client.get(url, HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 200
        assert_no_cache_header(resp)

        page = pq(resp.content)
        assert page.find('.description').text() == self.key1.description

        resp = self.client.post(url, follow=False, HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 302
        assert_no_cache_header(resp)

        assert Key.objects.filter(pk=self.key1.pk).count() == 0


class KeyViewsPermissionTest(RefetchingUserTestCase):

    def setUp(self):
        username = 'tester23'
        password = 'trustno1'
        email = 'tester23@example.com'

        self.user = user(username=username, email=email,
                         password=password, save=True)
        self.client.login(username=username, password=password)

    def test_new_key_requires_permission(self):
        url = reverse('authkeys.new')
        resp = self.client.get(url, HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 403
        assert_no_cache_header(resp)

        perm = Permission.objects.get(codename='add_key')
        self.user.user_permissions.add(perm)
        self._cache_bust_user_perms()

        resp = self.client.get(url, HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 200
        assert_no_cache_header(resp)

    def test_delete_key_requires_separate_permission(self):
        self.key1 = Key(user=self.user, description='Test Key 1')
        self.key1.save()

        url = reverse('authkeys.delete', args=(self.key1.pk,))
        resp = self.client.get(url, HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 403
        assert_no_cache_header(resp)
        self._cache_bust_user_perms()

        resp = self.client.get(url, HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 403
        assert_no_cache_header(resp)

        perm = Permission.objects.get(codename='delete_key')
        self.user.user_permissions.add(perm)
        self._cache_bust_user_perms()

        resp = self.client.get(url, HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 200
        assert_no_cache_header(resp)


@pytest.mark.parametrize('endpoint', ['new', 'list', 'history', 'delete'])
def test_redirect(client, endpoint):
    url = reverse('authkeys.{}'.format(endpoint),
                  args=(1,) if endpoint in ('history', 'delete') else ())
    response = client.get(url)
    assert_redirect_to_wiki(response, url)
