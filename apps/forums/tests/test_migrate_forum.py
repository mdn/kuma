from datetime import datetime

from django.core import management
from django.test import TestCase
from django.contrib.auth.models import User

from nose.tools import eq_

from forums.models import Forum, Thread, Post
from sumo.models import (Forum as TikiForum, ForumThread as TikiThread,
                         TikiUser)


class MigrateForumTestCase(TestCase):
    fixtures = ['users.json', 'tikiusers.json', 'discussion_forums.json']

    def setUp(self):
        management.call_command('migrate_forum', 3, 4, 5, verbosity=0)
        # migrated threads
        self.t1 = Thread.objects.get(pk=307195)
        self.t2 = Thread.objects.get(pk=305015)
        self.t3 = Thread.objects.get(pk=307862)
        self.t4 = Thread.objects.get(pk=308011)
        self.t5 = Thread.objects.get(pk=310169)

        # tiki threads
        self.tiki_t1 = TikiThread.objects.get(pk=307195)
        self.tiki_t2 = TikiThread.objects.get(pk=305015)
        self.tiki_t3 = TikiThread.objects.get(pk=307862)

        # posts
        self.p1 = self.t1.post_set.all()[1]

    def test_all_migrated(self):
        """All content was migrated."""
        eq_(3, Forum.objects.all().count())
        eq_(7, Thread.objects.all().count())
        eq_(21, Post.objects.all().count())

    def test_forums(self):
        """Forums were migrated correctly."""
        fs = []
        for tiki_f in TikiForum.objects.all():
            try:
                fs.append(Forum.objects.get(name=tiki_f.name))
            except Forum.DoesNotExist:
                self.fail('Forum %s not migrated correctly.' % tiki_f.name)

        f_slugs = ('contributors', 'off-topic', 'knowledge-base-articles')
        for f in fs:
            self.assertNotEquals(0, len(f.name))
            assert f.slug in f_slugs, 'Unexpected slug "%s"' % f.slug
            self.assertNotEquals(0, len(f.description))

    def test_fake_user(self):
        """Anonymous user exists in both models."""
        anonymous_name = 'AnonymousUser'
        try:
            User.objects.get(username=anonymous_name)
        except User.DoesNotExist:
            self.fail(anonymous_name)
        try:
            TikiUser.objects.get(login=anonymous_name)
        except TikiUser.DoesNotExist:
            self.fail('Tiki %s not created.' % anonymous_name)

    def test_thread_forum(self):
        """Thread's forum is properly set."""
        eq_('contributors', self.t1.forum.slug)

    def test_thread_title(self):
        """Thread's title is properly set."""
        expected = self.tiki_t1.title
        eq_(expected, self.t1.title)

    def test_thread_last_post(self):
        """Thread's last post is properly set."""
        # Check by timestamp
        t = TikiThread.objects.order_by('-commentDate').filter(
                parentId=self.tiki_t1.threadId)[0]
        expected = datetime.fromtimestamp(t.commentDate)
        eq_(expected, self.t1.last_post.created)

    def test_thread_creator(self):
        """Thread's creator is properly set."""
        expected = self.tiki_t1.userName
        eq_(expected, self.t1.creator.username)

    def test_thread_created(self):
        """Thread's created date is properly set."""
        expected = datetime.fromtimestamp(self.tiki_t1.commentDate)
        eq_(expected, self.t1.created)

    def test_threads_belong(self):
        """Threads belong to their corresponding forums."""
        eq_(5, len(Thread.objects.filter(forum__slug='contributors')))

    def test_thread_content(self):
        """A thread's content is turned into the first post."""
        p = self.t1.post_set.all()[0]
        eq_('This is a thread with 10 replies.', p.content)

    def test_threads_normal(self):
        """Threads of type 'n' are not sticky or locked."""
        eq_(False, self.t1.is_sticky)
        eq_(False, self.t1.is_locked)

    def test_threads_sticky(self):
        """Threads of type 's' are sticky."""
        eq_(True, self.t3.is_sticky)
        eq_(False, self.t3.is_locked)

    def test_threads_locked(self):
        """Threads of type 'l' are locked."""
        eq_(False, self.t4.is_sticky)
        eq_(True, self.t4.is_locked)

    def test_threads_sticky_locked(self):
        """Threads of type 'a' are sticky and locked."""
        eq_(True, self.t5.is_sticky)
        eq_(True, self.t5.is_locked)

    def test_thread_replies(self):
        """Threads have the correct number of replies."""
        expected = (  # (thread_id, replies)
                    (307195, 10),
                    (305015, 2),
                    (307862, 0), )
        for thread_id, replies in expected:
            eq_(replies, Thread.objects.get(pk=thread_id).replies)

    def test_post_belongs(self):
        """Post belongs to thread."""
        posts = Post.objects.filter(thread=self.t2)
        eq_(3, len(posts))

    def test_post_content(self):
        """A post's content is converted correctly."""
        eq_('Oh [[the irony|what?]],\n# it did\n# it again \n<blockquote> '
            'while [submitting this] </blockquote>\nnew topic - but had '
            'ended up posting anyway.', self.p1.content)

    def test_post_author(self):
        """A post's author is properly set."""
        expected = User.objects.get(username='jsocol')
        eq_(expected, self.p1.author)

    def test_post_updated_by(self):
        """A post's updated_by is properly set."""
        expected = User.objects.get(username='jsocol')
        eq_(expected, self.p1.updated_by)

    def test_post_created(self):
        """Post's created date is properly set."""
        p = TikiThread.objects.order_by('commentDate').filter(
                parentId=self.tiki_t1.threadId)[0]
        expected = datetime.fromtimestamp(p.commentDate)
        migrated_p = self.t1.post_set.order_by('created')[1]
        eq_(expected, migrated_p.created)

    def test_post_updated(self):
        """Post's updated date is properly set."""
        p = TikiThread.objects.order_by('commentDate').filter(
                parentId=self.tiki_t1.threadId)[1]
        expected = datetime.fromtimestamp(p.commentDate)
        migrated_p = self.t1.post_set.order_by('created')[2]
        eq_(expected, migrated_p.updated)
