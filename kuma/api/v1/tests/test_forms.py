from django.test import RequestFactory

from kuma.api.v1.search.forms import SearchForm


def test_search_form_locale_happy_path():
    """The way the form handles 'locale' is a bit overly complicated.
    These unit tests focuses exclusively on that and when the form is valid."""

    initial = {"page": 1, "size": 10}
    request = RequestFactory().get("/api/v1/search?q=foo")
    form = SearchForm(request.GET, initial=initial)
    assert form.is_valid()
    assert form.cleaned_data["locale"] == []

    request = RequestFactory().get("/api/v1/search?q=foo")
    initial["locale"] = "ja"
    form = SearchForm(request.GET, initial=initial)
    assert form.is_valid()
    assert form.cleaned_data["locale"] == ["ja"]

    request = RequestFactory().get("/api/v1/search?q=foo&locale=Fr")
    form = SearchForm(request.GET, initial=initial)
    assert form.is_valid()
    assert form.cleaned_data["locale"] == ["Fr"]

    request = RequestFactory().get("/api/v1/search?q=foo&locale=Fr&locale=de")
    form = SearchForm(request.GET, initial=initial)
    assert form.is_valid()
    assert form.cleaned_data["locale"] == ["Fr", "de"]

    # Note, same as the initial default
    request = RequestFactory().get("/api/v1/search?q=foo&locale=ja")
    form = SearchForm(request.GET, initial=initial)
    assert form.is_valid()
    assert form.cleaned_data["locale"] == ["ja"]

    request = RequestFactory().get("/api/v1/search?q=foo&locale=ja&locale=fr")
    form = SearchForm(request.GET, initial=initial)
    assert form.is_valid()
    assert form.cleaned_data["locale"] == ["ja", "fr"]


def test_search_form_locale_validation_error():
    """The way the form handles 'locale' is a bit overly complicated.
    These unit tests focuses exclusively on that and when the form is NOT valid."""

    initial = {"page": 1, "size": 10}
    request = RequestFactory().get("/api/v1/search?q=foo&locale=xxx")
    form = SearchForm(request.GET, initial=initial)
    assert not form.is_valid()
    assert form.errors["locale"]

    request = RequestFactory().get("/api/v1/search?q=foo&locale=")
    form = SearchForm(request.GET, initial=initial)
    assert not form.is_valid()
    assert form.errors["locale"]
