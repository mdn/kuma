import pytest

from kuma.core.urlresolvers import reverse


@pytest.mark.django_db
def test_view_indexes(client, settings, wiki_user):
    """Test that looking at the list of Indexes doesn't reveal the
    username:password from any 'settings.ES_URLS'.
    """
    wiki_user.is_staff = True
    wiki_user.is_superuser = True
    wiki_user.set_password('secret')
    wiki_user.save()
    client.login(username=wiki_user.username, password='secret')

    settings.ES_URLS = [
        'localhost:9200',
        'https://uuuuser:passsw@remote.example.com:9200/prefix'
    ]

    url = reverse('admin:search_index_changelist')
    response = client.get(url)
    assert response.status_code == 200
    assert settings.ES_URLS[0] in response.content
    assert settings.ES_URLS[1] not in response.content
    assert settings.ES_URLS[1].replace(
        'uuuuser:passsw',
        'username:secret'
    ) in response.content
