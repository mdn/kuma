from nose.tools import eq_

from django.contrib.contenttypes.models import ContentType

from notifications.events import Event
from notifications.models import Watch
from notifications.tests import watch, watch_filter, ModelsTestCase
from notifications.tests.models import MockModel
from sumo.tests import TestCase
from users.tests import user


TYPE = 'some event'


class SimpleEvent(Event):
    event_type = TYPE


class ContentTypeEvent(SimpleEvent):
    content_type = ContentType  # saves mocking a model


class FilteredEvent(SimpleEvent):
    filters = set(['color', 'flavor'])


class FilteredContentTypeEvent(ContentTypeEvent):
    filters = set(['color', 'flavor'])


def emails_eq(addresses, event, **filters):
    """Assert that the given emails are the ones watched by `event`, given the
    scoping in `filters`."""
    eq_(set(addresses),
        set(u.email for u in event._users_watching_by_filter(**filters)))


class TestUsersWatching(TestCase):
    """Unit tests for Event._users_watching_by_filter()"""

    def test_simple(self):
        """Test whether a watch scoped only by event type fires for both
        anonymous and registered users."""
        registered_user = user(email='regist@ered.com', save=True)
        watch(event_type=TYPE, user=registered_user).save()
        watch(event_type=TYPE, email='anon@ymous.com').save()
        watch(event_type='something else', email='never@fires.com').save()
        emails_eq(['regist@ered.com', 'anon@ymous.com'], SimpleEvent())

    def test_unconfirmed(self):
        """Make sure unconfirmed watches don't fire."""
        watch(event_type=TYPE, email='anon@ymous.com', secret='x' * 10).save()
        watch(event_type=TYPE, email='confirmed@one.com').save()
        emails_eq(['confirmed@one.com'], SimpleEvent())

    def test_content_type(self):
        """Make sure watches filter properly by content type."""
        watch_type = ContentType.objects.get_for_model(Watch)
        content_type_type = ContentType.objects.get_for_model(ContentType)
        registered_user = user(email='regist@ered.com', save=True)
        watch(event_type=TYPE, content_type=content_type_type,
              user=registered_user).save()
        watch(event_type=TYPE, content_type=content_type_type,
              email='anon@ymous.com').save()
        watch(event_type=TYPE, content_type=watch_type,
              email='never@fires.com').save()
        emails_eq(['regist@ered.com', 'anon@ymous.com'],
                   ContentTypeEvent())

    def test_filtered(self):
        """Make sure watches cull properly by additional filters."""
        # A watch with just the filter we're searching for:
        registered_user = user(email='ex@act.com', save=True)
        exact_watch = watch(event_type=TYPE, user=registered_user, save=True)
        watch_filter(watch=exact_watch, name='color', value=1).save()

        # A watch with extra filters:
        extra_watch = watch(event_type=TYPE, email='extra@one.com', save=True)
        watch_filter(watch=extra_watch, name='color', value=1).save()
        watch_filter(watch=extra_watch, name='flavor', value=2).save()

        # A watch with no row for the filter we're searching on:
        watch(event_type=TYPE, email='wild@card.com').save()

        # A watch with a mismatching filter--shouldn't be found
        mismatch_watch = watch(event_type=TYPE, email='mis@match.com',
                               save=True)
        watch_filter(watch=mismatch_watch, name='color', value=3).save()

        emails_eq(['ex@act.com', 'extra@one.com', 'wild@card.com'],
                    FilteredEvent(), color=1)

    def test_bad_filters(self):
        """Bad filter types passed in should throw TypeError."""
        # We have to actually iterate over the iterator to get it to do
        # anything.
        self.assertRaises(TypeError, list,
                          SimpleEvent()._users_watching_by_filter(smoo=3))


class TestNotification(TestCase):
    """Tests for Event methods that create, examine, and destroy watches."""

    def test_lifecycle(self):
        """Vet the creation, testing, and deletion of watches.

        Test registered users and anonymous email addresses. Test content_types
        and general filters.

        """
        EMAIL = 'fred@example.com'
        FilteredContentTypeEvent.notify(EMAIL, color=1)
        assert FilteredContentTypeEvent.is_notifying(EMAIL, color=1)

        FilteredContentTypeEvent.stop_notifying(EMAIL, color=1)
        assert not FilteredContentTypeEvent.is_notifying(EMAIL, color=1)

    def test_notify_idempotence(self):
        """Assure notify() returns an existing watch when possible."""
        u = user(save=True)
        w = FilteredContentTypeEvent.notify(u, color=3, flavor=4)
        eq_(w.pk, FilteredContentTypeEvent.notify(u, color=3, flavor=4).pk)
        eq_(1, Watch.objects.all().count())

    def test_duplicate_tolerance(self):
        """Assure notify() returns an existing watch if there is a matching
        one.

        Also make sure it returns only 1 watch even if there are duplicate
        matches.

        """
        w1 = watch(event_type=TYPE, email='hi@there.com', save=True)
        w2 = watch(event_type=TYPE, email='hi@there.com', save=True)
        assert SimpleEvent.notify('hi@there.com').pk in [w1.pk, w2.pk]

    def test_exact_matching(self):
        """Assert is_notifying() doesn't match watches having a superset of
        the given filters."""
        FilteredContentTypeEvent.notify('hi@there.com', color=3, flavor=4)
        assert not FilteredContentTypeEvent.is_notifying('hi@there.com',
                                                         color=3)


class TestCascadeDelete(ModelsTestCase):
    """Cascading deletes on object_id + content_type."""
    apps = ['notifications.tests']

    def test_mock_model(self):
        """Deleting an instance of MockModel should delete watches.

        Create instance of MockModel from notifications.tests.models, then
        delete it and watch the cascade go.

        """
        mock_m = MockModel.objects.create()
        watch(event_type=TYPE, email='hi@there.com', content_object=mock_m,
              save=True)
        MockModel.objects.all().delete()
        assert not Watch.objects.count(), 'Cascade delete failed.'
