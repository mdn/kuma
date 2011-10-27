from django.contrib.auth.models import User

import test_utils

from access.helpers import has_perm, has_perm_or_owns
from forums.models import Forum, Thread
from sumo.tests import TestCase
from funfactory.urlresolvers import reverse


class ForumTestPermissions(TestCase):
    """Make sure access helpers work on the forums."""

    fixtures = ['users.json', 'posts.json', 'forums_permissions.json']

    def setUp(self):
        url = reverse('forums.threads', args=[u'test-forum'])
        self.context = {'request': test_utils.RequestFactory().get(url)}
        self.forum_1 = Forum.objects.get(pk=1)
        self.forum_2 = Forum.objects.get(pk=2)

    def test_has_perm_thread_edit(self):
        """
        User in ForumsModerator group can edit thread in forum_1, but not in
        forum_2.
        """
        self.context['request'].user = User.objects.get(pk=47963)
        assert has_perm(self.context, 'forums_forum.thread_edit_forum',
                        self.forum_1)
        assert not has_perm(self.context, 'forums_forum.thread_edit_forum',
                            self.forum_2)

    def test_has_perm_or_owns_thread_edit(self):
        """
        User in ForumsModerator group can edit thread in forum_1, but not in
        forum_2.
        """
        me = User.objects.get(pk=118533)
        my_t = Thread.objects.filter(creator=me)[0]
        other_t = Thread.objects.exclude(creator=me)[0]
        self.context['request'].user = me
        perm = 'forums_forum.thread_edit_forum'
        assert has_perm_or_owns(self.context, perm, my_t, self.forum_1)
        assert not has_perm_or_owns(self.context, perm, other_t, self.forum_1)

    def test_has_perm_thread_delete(self):
        """
        User in ForumsModerator group can delete thread in forum_1, but not in
        forum_2.
        """
        self.context['request'].user = User.objects.get(pk=47963)
        assert has_perm(self.context, 'forums_forum.thread_delete_forum',
                        self.forum_1)
        assert not has_perm(self.context, 'forums_forum.thread_delete_forum',
                            self.forum_2)

    def test_has_perm_thread_sticky(self):
        """
        User in ForumsModerator group can change sticky status of thread in
        forum_1, but not in forum_2.
        """
        self.context['request'].user = User.objects.get(pk=47963)
        assert has_perm(self.context, 'forums_forum.thread_sticky_forum',
                        self.forum_1)
        assert not has_perm(self.context, 'forums_forum.thread_sticky_forum',
                            self.forum_2)

    def test_has_perm_thread_locked(self):
        """
        Sanity check: ForumsModerator group has no permission to change locked
        status in forum_1.
        """
        self.context['request'].user = User.objects.get(pk=47963)
        assert not has_perm(self.context, 'forums_forum.thread_locked_forum',
                            self.forum_1)

    def test_has_perm_post_edit(self):
        """
        User in ForumsModerator group can edit any post in forum_1, but not
        in forum_2.
        """
        self.context['request'].user = User.objects.get(pk=47963)
        assert has_perm(self.context, 'forums_forum.post_edit_forum',
                        self.forum_1)
        assert not has_perm(self.context, 'forums_forum.post_edit_forum',
                            self.forum_2)

    def test_has_perm_post_delete(self):
        """
        User in ForumsModerator group can delete any post in forum_1, but not
        in forum_2.
        """
        self.context['request'].user = User.objects.get(pk=47963)
        assert has_perm(self.context, 'forums_forum.post_delete_forum',
                        self.forum_1)
        assert not has_perm(self.context, 'forums_forum.post_delete_forum',
                            self.forum_2)

    def test_no_perm_thread_delete(self):
        """
        User not in ForumsModerator group cannot delete thread in any forum.
        """
        self.context['request'].user = User.objects.get(pk=118533)
        assert not has_perm(self.context, 'forums_forum.thread_delete_forum',
                            self.forum_1)
        assert not has_perm(self.context, 'forums_forum.thread_delete_forum',
                            self.forum_2)
