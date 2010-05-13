from nose.tools import eq_

from django.test import client

from forums.models import Forum, Thread, Post
from forums.tests import ForumTestCase
from sumo.urlresolvers import reverse
from sumo.helpers import urlparams


class ForumModelTestCase(ForumTestCase):

    def setUp(self):
        super(ForumModelTestCase, self).setUp()

        # Warm up the prefixer for reverse()
        client.Client().get('/')

    def test_forum_absolute_url(self):
        f = Forum.objects.get(pk=1)
        exp_ = reverse('forums.threads', kwargs={'forum_slug': f.slug})
        eq_(exp_, f.get_absolute_url())

    def test_thread_absolute_url(self):
        t = Thread.objects.get(pk=1)
        exp_ = reverse('forums.posts', kwargs={'forum_slug': t.forum.slug,
                                               'thread_id': t.id})
        eq_(exp_, t.get_absolute_url())

    def test_post_absolute_url(self):
        p = Post.objects.get(pk=1)
        url_ = reverse('forums.posts',
                       kwargs={'forum_slug': p.thread.forum.slug,
                               'thread_id': p.thread.id})
        exp_ = urlparams(url_, hash='post-%s' % p.id)
        eq_(exp_, p.get_absolute_url())

        p = Post.objects.get(pk=24)
        url_ = reverse('forums.posts',
                       kwargs={'forum_slug': p.thread.forum.slug,
                               'thread_id': p.thread.id})
        exp_ = urlparams(url_, hash='post-%s' % p.id, page=2)
        eq_(exp_, p.get_absolute_url())

    def test_post_page(self):
        p = Post.objects.get(pk=1)
        eq_(1, p.page)
        p = Post.objects.get(pk=22)
        eq_(1, p.page)
        p = Post.objects.get(pk=24)
        eq_(2, p.page)
