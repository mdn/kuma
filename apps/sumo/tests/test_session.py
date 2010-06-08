from datetime import datetime

from django.contrib.auth.models import User, AnonymousUser

from test_utils import TestCase

from sumo import backends
from sumo.models import Session, TikiUser
from sumo.urlresolvers import reverse


class SessionTestCase(TestCase):

    fixtures = ['sessions.json', 'tikiusers.json', 'users.json']

    def test_login(self):
        """
        Given a known tiki cookie, see if we can visit the site and appear
        logged in.
        """
        # Log in using cookie
        client = self.client
        client.cookies['SUMOv1'] = '57ad07b35736fc2b64ed62336fb3c2d2'
        response = client.get(reverse('search'), follow=True)
        self.assertContains(response, 'tiki-logout.php')

        # Test that the data copied over correctly.
        user = User.objects.get(pk=118533)
        tiki_user = TikiUser.objects.get(pk=118533)

        self.assertEqual(user.id, tiki_user.userId)
        self.assertEqual(user.username, tiki_user.login)
        self.assertEqual(user.email, tiki_user.email)
        self.assertEquals(user.date_joined,
            datetime.fromtimestamp(tiki_user.registrationDate))

    def test_backend_get_user_notexist(self):
        """If user_id does not exist, return none"""
        s = backends.SessionBackend()
        self.assertEqual(None, s.get_user(12))

    def test_invalid_session_reference(self):
        self.assertEqual(False, self.client.login(session=Session(pk='abcd')))

    def test_invalid_session_data(self):
        # If the session we reference refers to a missing user,
        # login should return False
        session = Session.objects.get(pk='ghiz4415d69ctlro2f02a14291m82l91')
        self.assertEqual(False, self.client.login(session=session))

        # Check that it's no longer in the db.
        f = lambda: Session.objects.get(pk='ghiz4415d69ctlro2f02a14291m82l91')
        self.assertRaises(Session.DoesNotExist, f)

    def test_middleware_invalid_session(self):
        client = self.client
        client.cookies['SUMOv1'] = 'badcookie'
        response = client.get('/en-US/search')
        assert isinstance(response.context['user'], AnonymousUser)
