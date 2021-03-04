from kuma.core.urlresolvers import reverse


def test_google_analytics_disabled(db, settings, client):
    settings.GOOGLE_ANALYTICS_ACCOUNT = None
    response = client.get(reverse("home"), follow=True)
    assert 200 == response.status_code
    assert b"ga('create" not in response.content


def test_google_analytics_enabled(db, settings, client):
    settings.GOOGLE_ANALYTICS_ACCOUNT = "UA-99999999-9"
    response = client.get(reverse("home"), follow=True)
    assert 200 == response.status_code
    assert b"ga('create" in response.content
