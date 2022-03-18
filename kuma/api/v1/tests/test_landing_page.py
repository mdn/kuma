import pytest

from kuma.core.urlresolvers import reverse
from kuma.plus.models import LandingPageSurvey


@pytest.mark.django_db
def test_ping_landing_page_survey_bad_request(client):
    url = reverse("api-v1:plus.landing_page.survey")

    # Not a valid UUID
    response = client.get(url, {"uuid": "xxx"})
    assert response.status_code == 422

    # Not a recognized UUID
    response = client.get(url, {"uuid": "88f7a689-454a-4647-99bf-d62fa66da24a"})
    assert response.status_code == 404

    # No UUID in post
    response = client.post(url)
    assert response.status_code == 422

    response = client.get(url, {"variant": "1"})
    assert response.status_code == 200
    # Invalid JSON
    response = client.post(url, {"uuid": response.json()["uuid"], "response": "{{{{"})
    assert response.status_code == 422


@pytest.mark.django_db
def test_ping_landing_page_survey_reuse_uuid(client):
    url = reverse("api-v1:plus.landing_page.survey")
    response1 = client.get(url, HTTP_CLOUDFRONT_VIEWER_COUNTRY_NAME="Sweden")
    assert response1.status_code == 200
    assert LandingPageSurvey.objects.all().count() == 1
    response2 = client.get(
        url,
        {"uuid": response1.json()["uuid"]},
        HTTP_CLOUDFRONT_VIEWER_COUNTRY_NAME="USA",
    )
    assert response2.json()["uuid"] == response1.json()["uuid"]
    assert LandingPageSurvey.objects.all().count() == 1
