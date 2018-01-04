'''Tests for kuma/wiki/views/edit.py'''
import pytest
from waffle.models import Flag

from kuma.core.models import IPBan
from kuma.core.urlresolvers import reverse


@pytest.fixture
def editor_client(client, wiki_user):
    Flag.objects.create(name='kumaediting', everyone=True)
    wiki_user.set_password('password')
    wiki_user.save()
    assert client.login(username=wiki_user.username, password='password')
    return client


def test_edit_get(editor_client, root_doc):
    url = reverse('wiki.edit', locale='en-US', args=[root_doc.slug])
    response = editor_client.get(url)
    assert response.status_code == 200


@pytest.mark.parametrize('method', ('GET', 'POST'))
def test_edit_banned_ip_not_allowed(method, editor_client, root_doc,
                                    cleared_cacheback_cache):
    ip = '127.0.0.1'
    IPBan.objects.create(ip=ip)
    url = reverse('wiki.edit', locale='en-US', args=[root_doc.slug])
    caller = getattr(editor_client, method.lower())
    response = caller(url, REMOTE_ADDR=ip)
    assert response.status_code == 403
