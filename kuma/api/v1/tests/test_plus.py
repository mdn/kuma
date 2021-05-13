import json

import pytest

from kuma.core.urlresolvers import reverse
from kuma.plus.models import LandingPageSurvey


@pytest.mark.django_db
def test_ping_landing_page_survey_happy_path(client):
    url = reverse("api.v1.plus.landing_page_survey")
    response = client.get(
        url, {"variant": 1}, HTTP_CLOUDFRONT_VIEWER_COUNTRY_NAME="Antartica"
    )
    assert response.status_code == 200
    (result,) = LandingPageSurvey.objects.all()
    assert result.variant == 1
    assert not result.email
    assert not result.response
    assert result.geo_information == "Antartica"

    # Now fill it with an email
    response = client.post(
        url,
        {"variant": 1, "uuid": str(result.uuid), "email": " peterbe@example.com  "},
    )
    assert response.status_code == 200
    (result,) = LandingPageSurvey.objects.all()
    assert result.variant == 1
    assert result.email == "peterbe@example.com"
    assert not result.response

    # Now fill it with a response
    response = client.post(
        url,
        {
            "variant": 1,
            "uuid": str(result.uuid),
            "response": json.dumps({"price": "perfect"}),
        },
    )
    assert response.status_code == 200
    (result,) = LandingPageSurvey.objects.all()
    assert result.variant == 1
    assert result.email == "peterbe@example.com"
    assert result.response == json.dumps({"price": "perfect"})


@pytest.mark.django_db
def test_ping_landing_page_survey_bad_request(client):
    url = reverse("api.v1.plus.landing_page_survey")

    # No ?variant=...
    response = client.get(url)
    assert response.status_code == 400

    # Not a valid number
    response = client.get(url, {"variant": "xxx"})
    assert response.status_code == 400

    # Not a valid UUID
    response = client.get(url, {"variant": 1, "uuid": "xxx"})
    assert response.status_code == 400

    # Not a recognized UUID
    response = client.get(
        url, {"variant": 1, "uuid": "88f7a689-454a-4647-99bf-d62fa66da24a"}
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_ping_landing_page_survey_reuse_uuid(client):
    url = reverse("api.v1.plus.landing_page_survey")
    response1 = client.get(
        url, {"variant": 1}, HTTP_CLOUDFRONT_VIEWER_COUNTRY_NAME="Sweden"
    )
    assert response1.status_code == 200
    assert LandingPageSurvey.objects.all().count() == 1
    response2 = client.get(
        url,
        {"variant": 1, "uuid": response1.json()["uuid"]},
        HTTP_CLOUDFRONT_VIEWER_COUNTRY_NAME="USA",
    )
    assert response2.json()["uuid"] == response1.json()["uuid"]
    assert LandingPageSurvey.objects.all().count() == 1


@pytest.mark.django_db
def test_ping_landing_page_survey_authenticated(user_client, wiki_user):
    url = reverse("api.v1.plus.landing_page_survey")
    response = user_client.get(url, {"variant": 1})
    assert response.status_code == 200
    (result,) = LandingPageSurvey.objects.all()
    assert result.user == wiki_user
