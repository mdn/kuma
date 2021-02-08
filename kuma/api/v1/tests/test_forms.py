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
    initial["locale"] = "sv-Se"
    form = SearchForm(request.GET, initial=initial)
    assert form.is_valid()
    assert form.cleaned_data["locale"] == ["sv-Se"]

    request = RequestFactory().get("/api/v1/search?q=foo&locale=Fr")
    form = SearchForm(request.GET, initial=initial)
    assert form.is_valid()
    assert form.cleaned_data["locale"] == ["Fr"]

    request = RequestFactory().get("/api/v1/search?q=foo&locale=Fr&locale=de")
    form = SearchForm(request.GET, initial=initial)
    assert form.is_valid()
    print(form.cleaned_data)
    assert form.cleaned_data["locale"] == ["Fr", "de"]

    # Note, same as the initial default
    request = RequestFactory().get("/api/v1/search?q=foo&locale=SV-se")
    form = SearchForm(request.GET, initial=initial)
    assert form.is_valid()
    assert form.cleaned_data["locale"] == ["SV-se"]

    request = RequestFactory().get("/api/v1/search?q=foo&locale=SV-se&locale=fr")
    form = SearchForm(request.GET, initial=initial)
    assert form.is_valid()
    assert form.cleaned_data["locale"] == ["SV-se", "fr"]


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
