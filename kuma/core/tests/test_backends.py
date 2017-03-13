import pytest
from mock import patch
from django.db import models
from constance.backends.database import DatabaseBackend
from kuma.core.backends import ReadOnlyConstanceDatabaseBackend


@pytest.mark.django_db
def test_read_only_constance_db_backend():
    from constance import settings

    with patch.object(settings, 'DATABASE_CACHE_BACKEND', new=None):

        rw_be = DatabaseBackend()
        with patch.object(models.Model, 'save') as save_mock:
            rw_be.set('x', 3)
            assert save_mock.called

        rw_be.set('x', 7)
        assert rw_be.get('x') == 7

        ro_be = ReadOnlyConstanceDatabaseBackend()
        with patch.object(models.Model, 'save') as save_mock:
            ro_be.set('y', 3)
            assert not save_mock.called

        ro_be.set('y', 3)
        assert ro_be.get('y') is None
        assert ro_be.get('x') == 7
