import pytest

from kuma.core.tests import assert_no_cache_header
from kuma.core.urlresolvers import reverse
from kuma.users.templatetags.jinja_helpers import gravatar_url


@pytest.mark.parametrize(
    'http_method', ['put', 'post', 'delete', 'options', 'head'])
def test_whoami_disallowed_methods(client, http_method):
    """HTTP methods other than GET are not allowed."""
    url = reverse('users.api.whoami')
    response = getattr(client, http_method)(url)
    assert response.status_code == 405
    assert_no_cache_header(response)


@pytest.mark.parametrize('timezone', ('US/Eastern', 'US/Pacific'))
def test_whoami_anonymous(client, settings, timezone):
    """Test response for anonymous users."""
    settings.TIME_ZONE = timezone
    url = reverse('users.api.whoami')
    response = client.get(url)
    assert response.status_code == 200
    assert response['content-type'] == 'application/json'
    assert response.json() == {
        'username': None,
        'timezone': timezone,
        'is_authenticated': False,
        'is_staff': False,
        'is_superuser': False,
        'is_beta_tester': False,
        'gravatar_url': {
            'small': None,
            'large': None,
        }
    }
    assert_no_cache_header(response)


@pytest.mark.parametrize(
    'timezone,is_staff,is_superuser,is_beta_tester',
    [('US/Eastern', False, False, False),
     ('US/Pacific', True, True, True)],
    ids=('muggle', 'wizard'))
def test_whoami(user_client, wiki_user, beta_testers_group, timezone, is_staff,
                is_superuser, is_beta_tester):
    """Test responses for logged-in users."""
    wiki_user.timezone = timezone
    wiki_user.is_staff = is_staff
    wiki_user.is_superuser = is_superuser
    wiki_user.is_staff = is_staff
    if is_beta_tester:
        wiki_user.groups.add(beta_testers_group)
    wiki_user.save()
    url = reverse('users.api.whoami')
    response = user_client.get(url)
    assert response.status_code == 200
    assert response['content-type'] == 'application/json'
    assert response.json() == {
        'username': wiki_user.username,
        'timezone': timezone,
        'is_authenticated': True,
        'is_staff': is_staff,
        'is_superuser': is_superuser,
        'is_beta_tester': is_beta_tester,
        'gravatar_url': {
            'small': gravatar_url(wiki_user.email, size=50),
            'large': gravatar_url(wiki_user.email, size=200),
        }
    }
    assert_no_cache_header(response)
