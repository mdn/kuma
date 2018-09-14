import pytest

from kuma.core.tests import assert_no_cache_header
from kuma.core.urlresolvers import reverse


@pytest.mark.django_db
def test_contribute_view(client, settings):
    '''If enabled, contribution page is returned.'''
    settings.MDN_CONTRIBUTION = True
    response = client.get(reverse('contribute'))
    assert_no_cache_header(response)
    assert response.status_code == 200


@pytest.mark.django_db
def test_contribute_view_404(client, settings):
    '''If diabled, contribution page is 404.'''
    settings.MDN_CONTRIBUTION = False
    response = client.get(reverse('contribute'))
    assert response.status_code == 404
