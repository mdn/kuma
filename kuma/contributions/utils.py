from django.conf import settings


def enabled():
    """Return True if contributions are enabled."""
    return settings.MDN_CONTRIBUTION
