from .forms import ContributionForm, ContributionRecurringPaymentForm
from .utils import enabled, popup_enabled, recurring_payment_enabled


def global_contribution_form(request):
    """Adds contribution form to the context."""
    if enabled(request):
        initial_data = {
            'name': request.user.get_full_name() or request.user.username,
            'email': request.user.email,
        } if request.user.is_authenticated else {}

        return {
            'contribution_enabled': True,
            'contribution_recurring_payment_enabled': recurring_payment_enabled(request),
            'contribution_popup': popup_enabled(request),
            'contribution_form': ContributionForm(initial=initial_data),
            'contribution_recurring_payment_form': ContributionRecurringPaymentForm(initial=initial_data),
            'hide_cta': True,
        }
    return {'contribution_enabled': False}
