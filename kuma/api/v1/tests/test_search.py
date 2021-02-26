import pytest
from elasticmock import FakeElasticsearch
from mock import patch

from kuma.core.urlresolvers import reverse


@pytest.mark.django_db
def test_search_validation_problems(user_client, settings):
    url = reverse("api.v1.search")

    # locale invalid
    response = user_client.get(url, {"q": "x", "locale": "xxx"})
    assert response.status_code == 400
    assert response.json()["errors"]["locale"][0]["code"] == "invalid_choice"
    # all non-200 OK responses should NOT have a Cache-Control header set.
    assert "cache-control" not in response

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

    # 'slug_prefix' has to be anything but empty
    response = user_client.get(url, {"q": "x", "slug_prefix": ""})
    assert response.status_code == 400
    assert response.json()["errors"]["slug_prefix"][0]["code"] == "invalid_choice"


class FindEverythingFakeElasticsearch(FakeElasticsearch):
    def search(self, *args, **kwargs):
        # This trick is what makes the mock so basic. It basically removes
        # any search query so that it just returns EVERYTHING that's been indexed.
        kwargs.pop("body", None)
        result = super().search(*args, **kwargs)
        # Due to a bug in ElasticMock, instead of returning an object for the
        # `response.hits.total`, it returns just an integer. We'll need to fix that.
        if isinstance(result["hits"]["total"], int):
            result["hits"]["total"] = {
                "value": result["hits"]["total"],
                "relation": "eq",
            }
        return result


@pytest.fixture
def mock_elasticsearch():
    fake_elasticsearch = FindEverythingFakeElasticsearch()
    with patch("elasticsearch_dsl.search.get_connection") as get_connection:
        get_connection.return_value = fake_elasticsearch
        yield fake_elasticsearch


def test_search_basic_match(user_client, settings, mock_elasticsearch):
    mock_elasticsearch.index(
        settings.SEARCH_INDEX_NAME,
        {
            "id": "/en-us/docs/Foo",
            "title": "Foo Title",
            "summary": "Foo summary",
            "locale": "en-us",
            "archived": False,
            "slug": "Foo",
            "popularity": 0,
        },
        id="/en-us/docs/Foo",
    )
    url = reverse("api.v1.search")
    response = user_client.get(url, {"q": "x"})
    assert response.status_code == 200
    assert "public" in response["Cache-Control"]
    assert "max-age=" in response["Cache-Control"]
    assert "max-age=0" not in response["Cache-Control"]

    assert response["content-type"] == "application/json"
    assert response["Access-Control-Allow-Origin"] == "*"
    data = response.json()
    assert data["metadata"]["page"] == 1
    assert data["metadata"]["size"]
    assert data["metadata"]["took_ms"]
    assert data["metadata"]["total"]["value"] == 1
    assert data["metadata"]["total"]["relation"] == "eq"
    assert data["suggestions"] == []
    assert data["documents"] == [
        {
            "archived": False,
            "highlight": {"body": [], "title": []},
            "locale": "en-us",
            "mdn_url": "/en-us/docs/Foo",
            "popularity": 0,
            "score": 1.0,
            "slug": "Foo",
            "title": "Foo Title",
            "summary": "Foo summary",
        }
    ]
