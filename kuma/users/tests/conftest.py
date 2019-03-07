import pytest

from django.contrib.auth.models import Group


@pytest.fixture
def beta_testers_group(db):
    return Group.objects.create(name='Beta Testers')
