from django.conf import settings
from waffle import flag_is_active

from .constants import CONTRIBUTION_BETA_FLAG


def enabled(request):
    """Return True if contributions are enabled."""
    return bool(settings.MDN_CONTRIBUTION)


def popup_enabled(request):
    """Returns True if the popup is enabled for the user."""
    return (enabled(request) and
            hasattr(request, 'user') and
            flag_is_active(request, CONTRIBUTION_BETA_FLAG))
