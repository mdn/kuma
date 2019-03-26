import pytest


@pytest.fixture
def api_settings(settings):
    settings.BETA_HOST = 'beta.mdn.dev'
    settings.ALLOWED_HOSTS.append(settings.BETA_HOST)
    settings.ENABLE_RESTRICTIONS_BY_HOST = True
    return settings
