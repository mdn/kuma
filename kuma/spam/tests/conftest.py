import pytest
from waffle.testutils import override_flag

from ..constants import SPAM_CHECKS_FLAG


@pytest.fixture
def spam_check_everyone(db):
    with override_flag(SPAM_CHECKS_FLAG, True):
        yield
