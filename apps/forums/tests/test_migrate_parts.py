from datetime import datetime

from nose.tools import eq_

from forums.management.commands.migrate_forum import (
    create_forum, create_thread, create_post)
from sumo.models import Forum as TikiForum, ForumThread as TikiThread
from sumo.tests import TestCase


def helper_create_forum():
    tiki_f = TikiForum.objects.get(forumId=3)
    return create_forum(tiki_f)


def helper_create_thread(tiki_t):
    f = helper_create_forum()
    return (f, create_thread(f, tiki_t))


class MigrateManualTestCase(TestCase):
    fixtures = ['users.json', 'tikiusers.json', 'discussion_forums.json']

    def test_forums(self):
        """create_forum works correctly."""
        f = helper_create_forum()

        self.assertNotEquals(0, len(f.name))
        eq_('contributors', f.slug)
        self.assertNotEquals(0, len(f.description))

    def test_thread_basic(self):
        """create_thread basic fields are set properly."""
        tiki_t = TikiThread.objects.get(pk=307195)
        f, t = helper_create_thread(tiki_t)

        p = t.post_set.all()[0]
        created_date = datetime.fromtimestamp(tiki_t.commentDate)

        eq_(f, t.forum)
        eq_(tiki_t.title, t.title)
        eq_(False, t.is_sticky)
        eq_(False, t.is_locked)
        eq_(p, t.last_post)
        eq_(tiki_t.userName, t.creator.username)
        eq_(created_date, t.created)
        eq_(0, t.replies)
        self.assertNotEquals('', p.content)

    def test_thread_sticky(self):
        """create_thread sets is_sticky properly."""
        tiki_t = TikiThread.objects.filter(type='s', parentId=0)[0]
        f, t = helper_create_thread(tiki_t)

        eq_(True, t.is_sticky)
        eq_(False, t.is_locked)

    def test_thread_locked(self):
        """create_thread sets is_locked properly."""
        tiki_t = TikiThread.objects.filter(type='l', parentId=0)[0]
        f, t = helper_create_thread(tiki_t)

        eq_(False, t.is_sticky)
        eq_(True, t.is_locked)

    def test_thread_sticky_locked(self):
        """create_thread sets locked and sticky properly."""
        tiki_t = TikiThread.objects.filter(type='a', parentId=0)[0]
        f, t = helper_create_thread(tiki_t)

        eq_(True, t.is_sticky)
        eq_(True, t.is_locked)

    def test_thread_replies(self):
        """create_post sets replies."""
        tiki_t = TikiThread.objects.filter(parentId=0)[0]
        f, t = helper_create_thread(tiki_t)

        tiki_p = TikiThread.objects.filter(parentId=tiki_t.threadId)[0]
        # create the post 3 times
        for i in range(3):
            create_post(t, tiki_p)
        # test the number of replies is 3
        eq_(3, t.replies)

    def test_post_basic(self):
        tiki_t = TikiThread.objects.get(pk=307195)
        f, t = helper_create_thread(tiki_t)

        tiki_p = TikiThread.objects.filter(parentId=tiki_t.threadId)[5]
        p = create_post(t, tiki_p)

        created_date = datetime.fromtimestamp(tiki_p.commentDate)

        eq_(t, p.thread)
        eq_(tiki_p.userName, p.author.username)
        eq_(tiki_p.userName, p.updated_by.username)
        eq_(created_date, p.created)
        eq_(created_date, p.updated)
        self.assertNotEquals('', p.content)
