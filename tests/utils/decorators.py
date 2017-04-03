import pytest


skip_if_maintenance_mode = pytest.mark.skipif(
    pytest.config.getoption('--maintenance-mode'),
    reason='the server is in maintenance mode'
)


skip_if_not_maintenance_mode = pytest.mark.skipif(
    not pytest.config.getoption('--maintenance-mode'),
    reason='the server is not in maintenance mode'
)
