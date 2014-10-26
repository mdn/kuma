from django.test import TestCase

from nose.tools import eq_, ok_
from pyquery import PyQuery as pq

from sumo.urlresolvers import reverse

from authkeys.models import Key
from authkeys.views import ITEMS_PER_PAGE

from kuma.users.tests import user


class KeyViewsTest(TestCase):

    def setUp(self):
        username = 'tester23'
        password = 'trustno1'
        self.email = 'tester23@example.com'

        self.user = user(username=username, email=self.email,
                         password=password, save=True)

        self.client.login(username=username, password=password)

        self.user2 = user(username='someone', email='someone@example.com',
                          save=True)

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
