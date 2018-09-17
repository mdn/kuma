from django.conf import settings

from kuma.contributions.forms import ContributionForm


def global_contribution_form(request):
    """Adds contribution form to the context."""
    if settings.MDN_CONTRIBUTION:
        return {
            'contribution_form': ContributionForm(),
            'hide_cta': True
        }
    return {}
