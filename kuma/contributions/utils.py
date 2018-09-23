from django.conf import settings
from waffle import flag_is_active

from .constants import CONTRIBUTION_BETA_FLAG


def enabled(request):
    """Return True if contributions are enabled."""
    return (settings.MDN_CONTRIBUTION and
            flag_is_active(request, CONTRIBUTION_BETA_FLAG))
