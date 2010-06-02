from django import test
from django.contrib.contenttypes.models import ContentType

from nose.tools import eq_

from notifications import create_watch, check_watch, destroy_watch
from notifications.models import EventWatch
from forums.models import Post, Thread


class WatchTestCase(test.TestCase):

    fixtures = ['users.json', 'posts.json', 'notifications.json']

    def setUp(self):
        self.ct = ContentType.objects.get_for_model(Post)

    def test_create_watch(self):
        """create_watch() should create a new EventWatch."""
        post = Post.objects.all()[1]
        rv = create_watch(Post, post.pk, 'noone@example.com')

        assert rv, 'EventWatch was not created.'

        watches = EventWatch.objects.filter(watch_id=post.pk,
                                            content_type=self.ct)
        eq_(1, len(watches))
        eq_('noone@example.com', watches[0].email)

    def test_double_create_watch(self):
        """create_watch() twice should return false."""
        post = Post.objects.all()[2]
        create_watch(Post, post.pk, 'fred@example.com')
        rv = create_watch(Post, post.pk, 'fred@example.com')

        assert not rv, 'create_watch() returned True.'

        watches = EventWatch.objects.filter(watch_id=post.pk,
                                            content_type=self.ct)
        eq_(1, len(watches))

    def test_create_invalid_watch(self):
        """Creating a watch on a non-existent objects should raise DNE."""
        x = lambda pk: create_watch(Post, pk, 'noone@example.com')
        self.assertRaises(Post.DoesNotExist, x, 1000)

    def test_check_watch_exists(self):
        """If a watch exists, check_watch() should return True."""
        w = EventWatch.objects.get(pk=1)
        assert check_watch(Thread, w.watch_id, w.email)

    def test_check_watch_not_exist(self):
        """If a watch doesn't exist, check_watch() should return False."""
        assert not check_watch(Thread, 1000, 'bad@example.com')

    def test_destroy_watch_exists(self):
        """Destroying a watch should return True, and work."""
        assert destroy_watch(Thread, 1, 'noone2@example.com')

        w = EventWatch.objects.filter(email='noone2@example.com')
        eq_(0, len(w))

    def test_destroy_watch_not_exist(self):
        """Destroying a non-existent watch should return False."""
        assert not destroy_watch(Thread, 1, 'bad@example.com')
