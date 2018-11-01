from .forms import ContributionForm, RecurringPaymentForm
from .utils import enabled, popup_enabled, recurring_payment_enabled


def global_contribution_form(request):
    """Adds contribution form to the context."""
    if enabled(request):
        initial_data = {}
        if hasattr(request, 'user'):
            initial_data = {
                'name': request.user.get_full_name() or request.user.username,
                'email': request.user.email,
            } if request.user.is_authenticated else {}

        return {
            'contribution_enabled': True,
            'recurring_payment_enabled': recurring_payment_enabled(request),
            'contribution_popup': popup_enabled(request),
            'contribution_form': ContributionForm(initial=initial_data),
            'recurring_payment_form': RecurringPaymentForm(initial=initial_data),
            'hide_cta': True,
        }
    return {'contribution_enabled': False}
