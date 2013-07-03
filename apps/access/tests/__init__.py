# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from django.contrib.auth.models import User

from nose.tools import eq_
import test_utils

import access
from forums.models import Forum, Thread
from sumo.tests import TestCase
from sumo.urlresolvers import reverse


class AccessTests(TestCase):
    """Test stuff in access/__init__.py"""
    fixtures = ['users.json', 'posts.json', 'forums_permissions.json']

    def setUp(self):
        url = reverse('forums.threads', args=[u'test-forum'])
        self.context = {'request': test_utils.RequestFactory().get(url)}
        self.forum_1 = Forum.objects.get(pk=1)
        self.forum_2 = Forum.objects.get(pk=2)

    def test_admin_perm_thread(self):
        """Super user can do anything on any forum."""
        admin = User.objects.get(pk=1)

        # Loop over all forums perms and both forums
        perms = ('thread_edit_forum', 'thread_delete_forum', 'post_edit_forum',
                 'thread_sticky_forum', 'thread_locked_forum',
                 'post_delete_forum')
        forums = (self.forum_1, self.forum_2)

        for perm in perms:
            for forum in forums:
                assert access.has_perm(admin, 'forums_forum.' + perm, forum)

    def test_util_has_perm_or_owns_sanity(self):
        """Sanity check for access.has_perm_or_owns."""
        me = User.objects.get(pk=118533)
        my_t = Thread.objects.filter(creator=me)[0]
        other_t = Thread.objects.exclude(creator=me)[0]
        perm = 'forums_forum.thread_edit_forum'
        allowed = access.has_perm_or_owns(me, perm, my_t, self.forum_1)
        eq_(allowed, True)
        allowed = access.has_perm_or_owns(me, perm, other_t, self.forum_1)
        eq_(allowed, False)

    def test_has_perm_per_object(self):
        """Assert has_perm checks per-object permissions correctly."""
        user = User.objects.get(pk=47963)
        perm = 'forums_forum.thread_edit_forum'
        assert access.has_perm(user, perm, self.forum_1)
        assert not access.has_perm(user, perm, self.forum_2)

    def test_perm_is_defined_on(self):
        """Test whether we check for permission relationship, independent of
        whether the permission is actually assigned to anyone."""
        perm = 'forums_forum.view_in_forum'
        assert access.perm_is_defined_on(perm, Forum.objects.get(pk=3))
        assert not access.perm_is_defined_on(perm, Forum.objects.get(pk=2))
