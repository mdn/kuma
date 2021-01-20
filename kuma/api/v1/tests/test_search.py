import pytest

from kuma.core.urlresolvers import reverse


@pytest.mark.django_db
def test_search_validation_problems(user_client, settings):
    url = reverse("api.v1.search")

    # locale invalid
    response = user_client.get(url, {"q": "x", "locale": "xxx"})
    assert response.status_code == 400
    assert response.json()["errors"]["locale"][0]["code"] == "invalid_choice"

    # 'q' exceeds max allowed characters
    response = user_client.get(url, {"q": "x" * (settings.ES_Q_MAXLENGTH + 1)})
    assert response.status_code == 400
    assert response.json()["errors"]["q"][0]["code"] == "max_length"

    # 'q' is empty or missing
    response = user_client.get(url, {"q": ""})
    assert response.status_code == 400
    assert response.json()["errors"]["q"][0]["code"] == "required"
    response = user_client.get(url)
    assert response.status_code == 400
    assert response.json()["errors"]["q"][0]["code"] == "required"

    # 'page' is not a valid number
    response = user_client.get(url, {"q": "x", "page": "x"})
    assert response.status_code == 400
    assert response.json()["errors"]["page"][0]["code"] == "invalid"
    response = user_client.get(url, {"q": "x", "page": "-1"})
    assert response.status_code == 400
    assert response.json()["errors"]["page"][0]["code"] == "min_value"

    # 'sort' not a valid value
    response = user_client.get(url, {"q": "x", "sort": "neverheardof"})
    assert response.status_code == 400
    assert response.json()["errors"]["sort"][0]["code"] == "invalid_choice"


def test_search_nothing_found(user_client):
    url = reverse("api.v1.search")

    response = user_client.get(url, {"q": "x"})
    assert response.status_code == 200
    assert response["content-type"] == "application/json"
    assert response["Access-Control-Allow-Origin"] == "*"
    data = response.json()
    from pprint import pprint

    pprint(data)

    assert 0


# class SearchViewTests(ElasticTestCase):
#     fixtures = ElasticTestCase.fixtures + ["wiki/documents.json", "search/filters.json"]

#     def test_search_basic(self):
#         url = reverse("api.v1.search", args=["en-US"])
#         response = self.client.get(url, {"q": "article"})
#         assert response.status_code == 200
#         assert response["content-type"] == "application/json"
#         assert response["Access-Control-Allow-Origin"] == "*"
#         data = response.json()
#         assert data["documents"]
#         assert data["count"] == 4
#         assert data["locale"] == "en-US"

#         # Now search in a non-en-US locale
#         response = self.client.get(url, {"q": "title", "locale": "fr"})
#         assert response.status_code == 200
#         assert response["content-type"] == "application/json"
#         data = response.json()
#         assert data["documents"]
#         assert data["count"] == 5
#         assert data["locale"] == "fr"
