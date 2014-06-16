from nose.tools import eq_

from notifications.models import Watch
from notifications.tasks import claim_watches
from notifications.tests import watch
from sumo.tests import TestCase
from kuma.users.tests import user


class ClaimWatchesTests(TestCase):
    def test_none(self):
        """No anonymous watches to claim."""
        u = user(email='some@bo.dy', save=True)
        claim_watches(u)
        # Nothing happens, but no error is raised either.

    def test_anonymous_only(self):
        """Make sure having mixed watches claims right ones."""
        # Watch some before registering.
        watch(email='some@bo.dy', save=True)
        watch(email='some@bo.dy', save=True)
        watch(email='no@bo.dy', save=True)

        # Register.
        u = user(email='some@bo.dy', save=True)

        claim_watches(u)

        # Original anonymous watch is claimed.
        assert not Watch.objects.filter(email='some@bo.dy').exists()
        eq_(2, Watch.objects.filter(email=None).count())
        eq_(2, Watch.objects.filter(user=u).count())

        # No other watches are affected.
        assert Watch.objects.filter(email='no@bo.dy').exists()

    def test_mixed(self):
        """Make sure having mixed watches claims right ones."""
        # Watch before registering.
        watch(email='some@bo.dy', save=True)
        watch(email='no@bo.dy', save=True)

        # Register nobody.
        user(email='no@bo.dy', save=True)

        # Then register somebody and watch something after registering.
        u = user(email='some@bo.dy', save=True)
        watch(user=u, save=True)

        claim_watches(u)

        # Original anonymous watch is claimed.
        assert not Watch.objects.filter(email='some@bo.dy').exists()
        eq_(2, Watch.objects.filter(email=None).count())

        # No other watches are affected.
        assert Watch.objects.filter(email='no@bo.dy').exists()
