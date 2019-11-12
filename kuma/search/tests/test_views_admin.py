import pytest

from kuma.core.urlresolvers import reverse


@pytest.mark.django_db
def test_view_indexes(admin_client, settings):
    """Test that looking at the list of Indexes doesn't reveal the
    username:password from any 'settings.ES_URLS'.
    """
    settings.ES_URLS = [
        'localhost:9200',
        'https://uuuuser:passsw@remote.example.com:9200/prefix'
    ]

    url = reverse('admin:search_index_changelist')
    response = admin_client.get(url)
    assert response.status_code == 200
    content = response.content.decode()
    assert settings.ES_URLS[0] in content
    assert settings.ES_URLS[1] not in content
    assert settings.ES_URLS[1].replace(
        'uuuuser:passsw',
        'username:secret'
    ) in content
