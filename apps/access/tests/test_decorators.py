from django.contrib.auth.models import User, AnonymousUser
from django.http import HttpResponse

from django.test import RequestFactory
from nose.tools import eq_

from kuma.users.tests import UserTestCase
from access.decorators import (logout_required, login_required,
                               permission_required)


def simple_view(request):
    return HttpResponse()


class LogoutRequiredTestCase(UserTestCase):
    rf = RequestFactory()

    def test_logged_out_default(self):
        request = self.rf.get('/foo')
        request.user = AnonymousUser()
        view = logout_required(simple_view)
        response = view(request)
        eq_(200, response.status_code)

    def test_logged_in_default(self):
        request = self.rf.get('/foo')
        request.user = User.objects.get(username='testuser')
        view = logout_required(simple_view)
        response = view(request)
        eq_(302, response.status_code)

    def test_logged_in_argument(self):
        request = self.rf.get('/foo')
        request.user = User.objects.get(username='testuser')
        view = logout_required('/bar')(simple_view)
        response = view(request)
        eq_(302, response.status_code)
        eq_('/bar', response['location'])


class LoginRequiredTestCase(UserTestCase):
    rf = RequestFactory()

    def test_logged_out_default(self):
        request = self.rf.get('/foo')
        request.user = AnonymousUser()
        view = login_required(simple_view)
        response = view(request)
        eq_(302, response.status_code)

    def test_logged_in_default(self):
        """Active user login."""
        request = self.rf.get('/foo')
        request.user = User.objects.get(username='testuser')
        view = login_required(simple_view)
        response = view(request)
        eq_(200, response.status_code)

    def test_logged_in_inactive(self):
        """Inactive user login not allowed by default."""
        request = self.rf.get('/foo')
        user = User.objects.get(username='testuser2')
        user.is_active = False
        request.user = user
        view = login_required(simple_view)
        response = view(request)
        eq_(302, response.status_code)

    def test_logged_in_inactive_allow(self):
        """Inactive user login explicitly allowed."""
        request = self.rf.get('/foo')
        user = User.objects.get(username='testuser2')
        user.is_active = False
        request.user = user
        view = login_required(simple_view, only_active=False)
        response = view(request)
        eq_(200, response.status_code)


class PermissionRequiredTestCase(UserTestCase):
    rf = RequestFactory()

    def test_logged_out_default(self):
        request = self.rf.get('/foo')
        request.user = AnonymousUser()
        view = permission_required('perm')(simple_view)
        response = view(request)
        eq_(302, response.status_code)

    def test_logged_in_default(self):
        request = self.rf.get('/foo')
        request.user = User.objects.get(username='testuser')
        view = permission_required('perm')(simple_view)
        response = view(request)
        eq_(403, response.status_code)

    def test_logged_in_inactive(self):
        """Inactive user is denied access."""
        request = self.rf.get('/foo')
        user = User.objects.get(username='admin')
        user.is_active = False
        request.user = user
        view = permission_required('perm')(simple_view)
        response = view(request)
        eq_(403, response.status_code)

    def test_logged_in_admin(self):
        request = self.rf.get('/foo')
        request.user = User.objects.get(username='admin')
        view = permission_required('perm')(simple_view)
        response = view(request)
        eq_(200, response.status_code)
