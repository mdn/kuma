from django import test
from django.contrib.auth.models import User, AnonymousUser

import test_utils

from notifications.helpers import is_watching
from notifications.models import EventWatch
from forums.models import Thread


class NotificationHelperTestCase(test.TestCase):

    fixtures = ['users.json', 'posts.json', 'notifications.json']

    def setUp(self):
        self.context = {'request': test_utils.RequestFactory().get('/')}

    def test_is_watching(self):
        """The is_watching helper should work correctly."""
        watcher = User.objects.get(pk=118533)
        nowatcher = User.objects.get(pk=47963)
        anon = AnonymousUser()

        thread = Thread.objects.get(pk=1)

        self.context['request'].user = watcher
        assert is_watching(self.context, thread)

        self.context['request'].user = nowatcher
        assert not is_watching(self.context, thread)

        self.context['request'].user = anon
        assert not is_watching(self.context, thread)
