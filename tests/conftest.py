from urlparse import urlsplit, urlunsplit

import pytest
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


_KUMA_STATUS = None
_DYNAMIC_FIXTURES = None


def pytest_addoption(parser):
    """Add command-line options for Kuma tests."""
    parser.addoption(
        "--maintenance-mode",
        action="store_true",
        help="run tests against a server in maintenance mode",
    )


def pytest_configure(config):
    """Configure pytest for the Kuma deployment under test."""
    global _KUMA_STATUS, _DYNAMIC_FIXTURES

    # The pytest-base-url plugin adds --base-url, and sets the default from
    # environment variable PYTEST_BASE_URL. If still unset, force to staging.
    if config.option.base_url is None:
        config.option.base_url = 'https://developer.allizom.org'
    base_url = config.getoption('base_url')

    # Process the server status from _kuma_status.json
    base_parts = urlsplit(base_url)
    kuma_status_url = urlunsplit((base_parts.scheme, base_parts.netloc,
                                  '_kuma_status.json', '', ''))
    session = requests.Session()
    retries = Retry(total=4, backoff_factor=0.1,
                    status_forcelist=[500, 502, 503, 504])
    session.mount(kuma_status_url, HTTPAdapter(max_retries=retries))
    response = session.get(kuma_status_url,
                           headers={'Accept': 'application/json'})
    response.raise_for_status()
    _KUMA_STATUS = response.json()
    _KUMA_STATUS['response'] = {'headers': response.headers}
    config._metadata['kuma'] = _KUMA_STATUS

    # Process the settings for this Kuma instance
    settings = _KUMA_STATUS['settings']
    allowed_hosts = set(settings['ALLOWED_HOSTS'])
    host_urls = set((base_url,))
    protocol = settings['PROTOCOL']
    for host in allowed_hosts:
        if host != '*':
            host_urls.add(protocol + host)

    # Setup dynamic fixtures
    _DYNAMIC_FIXTURES = {
        'any_host_url': {
            'argvalues': sorted(host_urls),
            'ids': [urlsplit(url).netloc for url in sorted(host_urls)]
        }
    }


def pytest_generate_tests(metafunc):
    """
    Handle dynamic parameterizaton of tests.

    Dynamic fixtures provided:
    - any_host_url - Any base URL provided by the Kuma deployment
    """
    for name, params in _DYNAMIC_FIXTURES.items():
        if name in metafunc.fixturenames:
            if type(params) is dict:
                metafunc.parametrize(name, **params)
            else:
                metafunc.parametrize(name, params)


@pytest.fixture(scope='session')
def is_local_url(base_url):
    """
    Returns True if the system-under-test is the local development
    instance (localhost).
    """
    return (base_url and
            urlsplit(base_url).hostname.split('.')[-1] == 'localhost')


@pytest.fixture(scope='session')
def kuma_status(base_url):
    return _KUMA_STATUS


@pytest.fixture(scope='session')
def is_debug(kuma_status):
    return kuma_status['settings']['DEBUG']


@pytest.fixture(scope='session')
def is_searchable(kuma_status):
    search = kuma_status['services']['search']
    return search['available'] and search['populated']


@pytest.fixture(scope='session')
def is_maintenance_mode(kuma_status):
    return kuma_status['settings']['MAINTENANCE_MODE']


@pytest.fixture(scope='session')
def is_behind_cdn(kuma_status):
    return 'x-amz-cf-id' in kuma_status['response']['headers']


@pytest.fixture(scope='session')
def site_url(kuma_status):
    return kuma_status['settings']['SITE_URL']


@pytest.fixture(scope='session')
def wiki_site_url(kuma_status):
    return kuma_status['settings']['WIKI_SITE_URL']
