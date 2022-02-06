import pytest
from django.http import HttpResponse
from django.views.decorators.cache import never_cache

from ..decorators import (
    redirect_in_maintenance_mode,
    shared_cache_control,
    skip_in_maintenance_mode,
)
from . import assert_no_cache_header


def simple_view(request):
    return HttpResponse()


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
