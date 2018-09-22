import mock
import pytest

from kuma.core.tests import assert_no_cache_header
from kuma.core.urlresolvers import reverse


@pytest.mark.django_db
@mock.patch('kuma.contributions.views.enabled')
def test_contribute_view(mock_enabled, client, settings):
    """If enabled, contribution page is returned."""
    mock_enabled.return_value = True
    response = client.get(reverse('contribute'))
    assert_no_cache_header(response)
    assert response.status_code == 200


@pytest.mark.django_db
@mock.patch('kuma.contributions.views.enabled')
def test_contribute_view_404(mock_enabled, client, settings):
    """If disabled, contribution page is 404."""
    mock_enabled.return_value = False
    response = client.get(reverse('contribute'))
    assert response.status_code == 404
