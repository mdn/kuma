import pytest

from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse

from django.test import RequestFactory

from kuma.core.decorators import (block_user_agents, logout_required,
                                  login_required, never_cache,
                                  redirect_in_maintenance_mode,
                                  permission_required)

from kuma.core.tests import KumaTestCase, eq_, ok_
from kuma.users.tests import UserTestCase


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
        request.user = self.user_model.objects.get(username='testuser')
        view = logout_required(simple_view)
        response = view(request)
        eq_(302, response.status_code)

    def test_logged_in_argument(self):
        request = self.rf.get('/foo')
        request.user = self.user_model.objects.get(username='testuser')
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
        request.user = self.user_model.objects.get(username='testuser')
        view = login_required(simple_view)
        response = view(request)
        eq_(200, response.status_code)

    def test_logged_in_inactive(self):
        """Inactive user login not allowed by default."""
        request = self.rf.get('/foo')
        user = self.user_model.objects.get(username='testuser2')
        user.is_active = False
        request.user = user
        view = login_required(simple_view)
        response = view(request)
        eq_(302, response.status_code)

    def test_logged_in_inactive_allow(self):
        """Inactive user login explicitly allowed."""
        request = self.rf.get('/foo')
        user = self.user_model.objects.get(username='testuser2')
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
        request.user = self.user_model.objects.get(username='testuser')
        view = permission_required('perm')(simple_view)
        response = view(request)
        eq_(403, response.status_code)

    def test_logged_in_inactive(self):
        """Inactive user is denied access."""
        request = self.rf.get('/foo')
        user = self.user_model.objects.get(username='admin')
        user.is_active = False
        request.user = user
        view = permission_required('perm')(simple_view)
        response = view(request)
        eq_(403, response.status_code)

    def test_logged_in_admin(self):
        request = self.rf.get('/foo')
        request.user = self.user_model.objects.get(username='admin')
        view = permission_required('perm')(simple_view)
        response = view(request)
        eq_(200, response.status_code)


class TestNeverCache(KumaTestCase):

    def test_never_cache(self):
        request = RequestFactory().get('/foo')
        view = never_cache(simple_view)
        response = view(request)
        eq_(200, response.status_code)
        [ok_(value in response['Cache-Control'])
         for value in ['no-cache', 'no-store', 'must-revalidate']]
        ok_('no-cache' in response['Pragma'])
        eq_('0', response['Expires'])


class TestBlockUserAgents(KumaTestCase):

    def setUp(self):
        self.request = RequestFactory().get('/foo')

    def test_regular_agent_ok(self):
        self.request.META['HTTP_USER_AGENT'] = 'Mozilla/5.0 (Windows NT 6.3;' \
            'WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
        self.view = block_user_agents(simple_view)
        response = self.view(self.request)
        eq_(200, response.status_code)

    def test_blocked_agents_forbidden(self):
        self.request.META['HTTP_USER_AGENT'] = 'curl/7.21.4 ' \
            '(universal-apple-darwin11.0) libcurl/7.21.4 OpenSSL/0.9.8r ' \
            'zlib/1.2.5'
        self.view = block_user_agents(simple_view)
        response = self.view(self.request)
        eq_(403, response.status_code)

        self.request.META['HTTP_USER_AGENT'] = 'Mozilla/5.0 (compatible; ' \
            'Yahoo! Slurp; http://help.yahoo.com/help/us/ysearch/slurp)'
        self.view = block_user_agents(simple_view)
        response = self.view(self.request)
        eq_(403, response.status_code)


@pytest.mark.parametrize(
    "maintenance_mode, request_method, methods, expected_status_code",
    [(True, 'get', None, 302),
     (True, 'post', None, 302),
     (False, 'get', None, 200),
     (False, 'post', None, 200),
     (True, 'get', ('PUT', 'POST'), 200),
     (True, 'put', ('PUT', 'POST'), 302),
     (True, 'post', ('PUT', 'POST'), 302),
     (False, 'get', ('PUT', 'POST'), 200),
     (False, 'put', ('PUT', 'POST'), 200),
     (False, 'post', ('PUT', 'POST'), 200),
     (False, 'post', ('PUT', 'POST'), 200)]
)
def test_redirect_in_maintenance_mode_decorator(rf, settings, maintenance_mode,
                                                request_method, methods,
                                                expected_status_code):
    request = getattr(rf, request_method)('/foo')
    settings.MAINTENANCE_MODE = maintenance_mode
    if methods is None:
        deco = redirect_in_maintenance_mode
    else:
        deco = redirect_in_maintenance_mode(methods=methods)
    resp = deco(simple_view)(request)
    assert resp.status_code == expected_status_code
