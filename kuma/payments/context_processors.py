import json

from .forms import ContributionForm, RecurringPaymentForm
from .utils import enabled, popup_enabled, recurring_payment_enabled

from django.conf import settings


def global_contribution_form(request):
    """Adds contribution form to the context."""
    if enabled(request):
        initial_data = {}
        if hasattr(request, 'user'):
            initial_data = {
                'name': request.user.fullname or request.user.username,
                'email': request.user.email,
            } if request.user.is_authenticated else {}

        return {
            'contribution_enabled': True,
            'recurring_payment_enabled': recurring_payment_enabled(request),
            'contribution_popup': popup_enabled(request),
            'contribution_form': ContributionForm(initial=initial_data),
            'recurring_payment_form': RecurringPaymentForm(initial=initial_data),
            'payments_form_donation_choices_json': json.dumps(settings.CONTRIBUTION_FORM_CHOICES),
            'recurring_payment_form_donation_choices_json': json.dumps(settings.RECURRING_PAYMENT_FORM_CHOICES),
            'hide_cta': True,
        }
    return {'contribution_enabled': False}
