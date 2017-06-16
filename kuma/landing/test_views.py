from kuma.core.urlresolvers import reverse


def test_contribute_json(client, db):
    response = client.get(reverse('contribute_json'))
    assert response.status_code == 200
    assert response['Content-Type'].startswith('application/json')


def test_home(client, db):
    response = client.get(reverse('home'), follow=True)
    assert response.status_code == 200


def test_promote_buttons(client, db):
    response = client.get(reverse('promote_buttons'), follow=True)
    assert response.status_code == 200
