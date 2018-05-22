import pytest
from waffle.models import Flag

from ..constants import SPAM_CHECKS_FLAG


@pytest.fixture
def spam_check_everyone(db):
    Flag.objects.update_or_create(
        name=SPAM_CHECKS_FLAG,
        defaults={'everyone': True}
    )
