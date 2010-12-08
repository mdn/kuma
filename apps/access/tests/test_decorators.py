from django.contrib.auth.models import User, AnonymousUser
from django.http import HttpResponse

from nose.tools import eq_
import test_utils

from access.decorators import (logout_required, login_required,
                               permission_required)
from sumo.tests import TestCase


def simple_view(request):
    return HttpResponse()


class LogoutRequiredTestCase(TestCase):
    fixtures = ['users.json']

    def test_logged_out_default(self):
        request = test_utils.RequestFactory().get('/foo')
        request.user = AnonymousUser()
        view = logout_required(simple_view)
        response = view(request)
        eq_(200, response.status_code)

    def test_logged_in_default(self):
        request = test_utils.RequestFactory().get('/foo')
        request.user = User.objects.get(username='jsocol')
        view = logout_required(simple_view)
        response = view(request)
        eq_(302, response.status_code)

    def test_logged_in_argument(self):
        request = test_utils.RequestFactory().get('/foo')
        request.user = User.objects.get(username='jsocol')
        view = logout_required('/bar')(simple_view)
        response = view(request)
        eq_(302, response.status_code)
        eq_('/bar', response['location'])


class LoginRequiredTestCase(TestCase):
    fixtures = ['users.json']

    def test_logged_out_default(self):
        request = test_utils.RequestFactory().get('/foo')
        request.user = AnonymousUser()
        view = login_required(simple_view)
        response = view(request)
        eq_(302, response.status_code)

    def test_logged_in_default(self):
        request = test_utils.RequestFactory().get('/foo')
        request.user = User.objects.get(username='jsocol')
        view = login_required(simple_view)
        response = view(request)
        eq_(200, response.status_code)


class PermissionRequiredTestCase(TestCase):
    fixtures = ['users.json']

    def test_logged_out_default(self):
        request = test_utils.RequestFactory().get('/foo')
        request.user = AnonymousUser()
        view = permission_required('perm')(simple_view)
        response = view(request)
        eq_(302, response.status_code)

    def test_logged_in_default(self):
        request = test_utils.RequestFactory().get('/foo')
        request.user = User.objects.get(username='jsocol')
        view = permission_required('perm')(simple_view)
        response = view(request)
        eq_(403, response.status_code)

    def test_logged_in_admin(self):
        request = test_utils.RequestFactory().get('/foo')
        request.user = User.objects.get(username='admin')
        view = permission_required('perm')(simple_view)
        response = view(request)
        eq_(200, response.status_code)
