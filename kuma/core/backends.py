from constance.backends.database import DatabaseBackend


class ReadOnlyConstanceDatabaseBackend(DatabaseBackend):
    """
    This class is intended as a drop-in read-only replacement for
    "constance.backends.database.DatabaseBackend" when specifying
    a value for the "CONSTANCE_BACKEND" Django setting. It effectively
    nullifies writes to the Constance database table(s).
    """

    def set(self, key, value):
        return
