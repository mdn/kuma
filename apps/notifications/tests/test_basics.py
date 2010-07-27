import hashlib

from django import test
from django.contrib.contenttypes.models import ContentType

from nose.tools import eq_

from notifications import create_watch, check_watch, destroy_watch
from notifications.models import EventWatch
from forums.models import Post, Thread
from sumo.urlresolvers import reverse
from sumo.helpers import urlparams


class WatchTestCase(test.TestCase):

    fixtures = ['users.json', 'posts.json', 'notifications.json']

    def setUp(self):
        self.ct = ContentType.objects.get_for_model(Post)

    def test_create_watch(self):
        """create_watch() should create a new EventWatch."""
        post = Post.objects.all()[1]
        rv = create_watch(Post, post.pk, 'noone@example.com', 'reply')

        assert rv, 'EventWatch was not created.'

        watches = EventWatch.objects.filter(watch_id=post.pk,
                                            content_type=self.ct)
        eq_(1, len(watches))
        eq_('noone@example.com', watches[0].email)

    def test_double_create_watch(self):
        """create_watch() twice should return false."""
        post = Post.objects.all()[2]
        create_watch(Post, post.pk, 'fred@example.com', 'reply')
        rv = create_watch(Post, post.pk, 'fred@example.com', 'reply')

        assert not rv, 'create_watch() returned True.'

        watches = EventWatch.objects.filter(watch_id=post.pk,
                                            content_type=self.ct)
        eq_(1, len(watches))

    def test_create_invalid_watch(self):
        """Creating a watch on a non-existent objects should raise DNE."""
        x = lambda pk: create_watch(Post, pk, 'noone@example.com', 'reply')
        self.assertRaises(Post.DoesNotExist, x, 1000)

    def test_check_watch_exists(self):
        """If a watch exists, check_watch() should return True."""
        w = EventWatch.objects.get(pk=1)
        assert check_watch(Thread, w.watch_id, w.email, 'reply')

    def test_check_watch_not_exist(self):
        """If a watch doesn't exist, check_watch() should return False."""
        assert not check_watch(Thread, 1000, 'bad@example.com', 'reply')

    def test_destroy_watch_exists(self):
        """Destroying a watch should return True, and work."""
        assert destroy_watch(Thread, 1, 'noone2@example.com', 'reply')

        w = EventWatch.objects.filter(email='noone2@example.com')
        eq_(0, len(w))

    def test_destroy_watch_not_exist(self):
        """Destroying a non-existent watch should return False."""
        assert not destroy_watch(Thread, 1, 'bad@example.com', 'reply')

    def test_key(self):
        """The EventWatch.key property is calculated correctly."""
        email = 'new@example.com'
        event_type = 'reply'
        ct = ContentType.objects.get_for_model(Thread)
        w = EventWatch(content_type=ct, watch_id=1, email=email,
                       event_type=event_type)
        sha = hashlib.sha1()
        key = '%s-%s-%s-%s' % (ct.id, 1, email, event_type)
        sha.update(key)
        eq_(sha.hexdigest(), w.key)

    def test_hash_set(self):
        """The EventWatch.hash property is set on save."""
        email = 'new@example.com'
        ct = ContentType.objects.get_for_model(Thread)
        w = EventWatch(content_type=ct, watch_id=1, email=email)
        w.save()
        assert w.hash
        eq_(w.key, w.hash)

    def test_remove_url(self):
        w = EventWatch.objects.all()[0]
        url_ = reverse('notifications.remove', args=[w.key])
        eq_(w.get_remove_url(), urlparams(url_, email=w.email))
