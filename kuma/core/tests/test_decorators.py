import pytest

from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from django.test import RequestFactory
from django.views.decorators.cache import never_cache

from kuma.users.tests import UserTestCase

from . import assert_no_cache_header, KumaTestCase
from ..decorators import (
    block_user_agents,
    login_required,
    logout_required,
    permission_required,
    redirect_in_maintenance_mode,
    shared_cache_control,
    skip_in_maintenance_mode,
)


def simple_view(request):
    return HttpResponse()


class LogoutRequiredTestCase(UserTestCase):
    rf = RequestFactory()

    def test_logged_out_default(self):
        request = self.rf.get("/foo")
        request.user = AnonymousUser()
        view = logout_required(simple_view)
        response = view(request)
        assert 200 == response.status_code

    def test_logged_in_default(self):
        request = self.rf.get("/foo")
        request.user = self.user_model.objects.get(username="testuser")
        view = logout_required(simple_view)
        response = view(request)
        assert 302 == response.status_code

    def test_logged_in_argument(self):
        request = self.rf.get("/foo")
        request.user = self.user_model.objects.get(username="testuser")
        view = logout_required("/bar")(simple_view)
        response = view(request)
        assert 302 == response.status_code
        assert "/bar" == response["location"]


class LoginRequiredTestCase(UserTestCase):
    rf = RequestFactory()

    def test_logged_out_default(self):
        request = self.rf.get("/foo")
        request.user = AnonymousUser()
        view = login_required(simple_view)
        response = view(request)
        assert 302 == response.status_code

    def test_logged_in_default(self):
        """Active user login."""
        request = self.rf.get("/foo")
        request.user = self.user_model.objects.get(username="testuser")
        view = login_required(simple_view)
        response = view(request)
        assert 200 == response.status_code

    def test_logged_in_inactive(self):
        """Inactive user login not allowed by default."""
        request = self.rf.get("/foo")
        user = self.user_model.objects.get(username="testuser2")
        user.is_active = False
        request.user = user
        view = login_required(simple_view)
        response = view(request)
        assert 302 == response.status_code

    def test_logged_in_inactive_allow(self):
        """Inactive user login explicitly allowed."""
        request = self.rf.get("/foo")
        user = self.user_model.objects.get(username="testuser2")
        user.is_active = False
        request.user = user
        view = login_required(simple_view, only_active=False)
        response = view(request)
        assert 200 == response.status_code


class PermissionRequiredTestCase(UserTestCase):
    rf = RequestFactory()

    def test_logged_out_default(self):
        request = self.rf.get("/foo")
        request.user = AnonymousUser()
        view = permission_required("perm")(simple_view)
        response = view(request)
        assert 302 == response.status_code

    def test_logged_in_default(self):
        request = self.rf.get("/foo")
        request.user = self.user_model.objects.get(username="testuser")
        view = permission_required("perm")(simple_view)
        response = view(request)
        assert 403 == response.status_code

    def test_logged_in_inactive(self):
        """Inactive user is denied access."""
        request = self.rf.get("/foo")
        user = self.user_model.objects.get(username="admin")
        user.is_active = False
        request.user = user
        view = permission_required("perm")(simple_view)
        response = view(request)
        assert 403 == response.status_code

    def test_logged_in_admin(self):
        request = self.rf.get("/foo")
        request.user = self.user_model.objects.get(username="admin")
        view = permission_required("perm")(simple_view)
        response = view(request)
        assert 200 == response.status_code


class TestBlockUserAgents(KumaTestCase):
    def setUp(self):
        self.request = RequestFactory().get("/foo")

    def test_regular_agent_ok(self):
        self.request.META["HTTP_USER_AGENT"] = (
            "Mozilla/5.0 (Windows NT 6.3;" "WOW64; rv:40.0) Gecko/20100101 Firefox/40.0"
        )
        self.view = block_user_agents(simple_view)
        response = self.view(self.request)
        assert 200 == response.status_code

    def test_blocked_agents_forbidden(self):
        self.request.META["HTTP_USER_AGENT"] = (
            "curl/7.21.4 "
            "(universal-apple-darwin11.0) libcurl/7.21.4 OpenSSL/0.9.8r "
            "zlib/1.2.5"
        )
        self.view = block_user_agents(simple_view)
        response = self.view(self.request)
        assert 403 == response.status_code

        self.request.META["HTTP_USER_AGENT"] = (
            "Mozilla/5.0 (compatible; "
            "Yahoo! Slurp; http://help.yahoo.com/help/us/ysearch/slurp)"
        )
        self.view = block_user_agents(simple_view)
        response = self.view(self.request)
        assert 403 == response.status_code


@pytest.mark.parametrize("maintenance_mode", [False, True])
def test_skip_in_maintenance_mode(settings, maintenance_mode):
    @skip_in_maintenance_mode
    def func(*args, **kwargs):
        return (args, sorted(kwargs.items()))

    settings.MAINTENANCE_MODE = maintenance_mode

    if maintenance_mode:
        assert func(1, 2, x=3, y=4) is None
    else:
        assert func(1, 2, x=3, y=4) == ((1, 2), [("x", 3), ("y", 4)])


@pytest.mark.parametrize(
    "maintenance_mode, request_method, methods, expected_status_code",
    [
        (True, "get", None, 302),
        (True, "post", None, 302),
        (False, "get", None, 200),
        (False, "post", None, 200),
        (True, "get", ("PUT", "POST"), 200),
        (True, "put", ("PUT", "POST"), 302),
        (True, "post", ("PUT", "POST"), 302),
        (False, "get", ("PUT", "POST"), 200),
        (False, "put", ("PUT", "POST"), 200),
        (False, "post", ("PUT", "POST"), 200),
        (False, "post", ("PUT", "POST"), 200),
    ],
)
def test_redirect_in_maintenance_mode_decorator(
    rf, settings, maintenance_mode, request_method, methods, expected_status_code
):
    request = getattr(rf, request_method)("/foo")
    settings.MAINTENANCE_MODE = maintenance_mode
    if methods is None:
        deco = redirect_in_maintenance_mode
    else:
        deco = redirect_in_maintenance_mode(methods=methods)
    resp = deco(simple_view)(request)
    assert resp.status_code == expected_status_code


def test_shared_cache_control_decorator_with_defaults(rf, settings):
    settings.CACHE_CONTROL_DEFAULT_SHARED_MAX_AGE = 777
    request = rf.get("/foo")
    response = shared_cache_control(simple_view)(request)
    assert response.status_code == 200
    assert "public" in response["Cache-Control"]
    assert "max-age=0" in response["Cache-Control"]
    assert "s-maxage=777" in response["Cache-Control"]


def test_shared_cache_control_decorator_with_overrides(rf, settings):
    settings.CACHE_CONTROL_DEFAULT_SHARED_MAX_AGE = 777
    request = rf.get("/foo")
    deco = shared_cache_control(max_age=999, s_maxage=0)
    response = deco(simple_view)(request)
    assert response.status_code == 200
    assert "public" in response["Cache-Control"]
    assert "max-age=999" in response["Cache-Control"]
    assert "s-maxage=0" in response["Cache-Control"]


def test_shared_cache_control_decorator_keeps_no_cache(rf, settings):
    request = rf.get("/foo")
    response = shared_cache_control(never_cache(simple_view))(request)
    assert response.status_code == 200
    assert "public" not in response["Cache-Control"]
    assert "s-maxage" not in response["Cache-Control"]
    assert_no_cache_header(response)
