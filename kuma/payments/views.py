# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from functools import wraps

from django.conf import settings
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt

from kuma.core.decorators import login_required

from .forms import ContributionForm, RecurringPaymentForm
from .tasks import payments_thank_you_email
from .utils import enabled, get_stripe_customer_data, cancel_stripe_customer_subscription


def skip_if_disabled(func):
    """If contributions are not enabled, then 404."""
    @wraps(func)
    def wrapped(request, *args, **kwargs):
        if enabled(request):
            return func(request, *args, **kwargs)
        raise Http404

    return wrapped


@skip_if_disabled
@never_cache
@csrf_exempt
def contribute(request):
    initial_data = {}
    if request.user.is_authenticated and request.user.email:
        initial_data = {
            'name': request.user.fullname,
            'email': request.user.email,
        }

    if request.POST:
        form = ContributionForm(request.POST)
        if form.is_valid():
            if form.make_charge():
                if settings.MDN_CONTRIBUTION_CONFIRMATION_EMAIL:
                    payments_thank_you_email.delay(
                        form.cleaned_data['name'],
                        form.cleaned_data['email']
                    )
                return redirect('payment_succeeded')
            return redirect('payment_error')

        form = ContributionForm(request.POST)
    else:
        form = ContributionForm(initial=initial_data)

    context = {
        'form': form,
        'hide_cta': True,
        'recurring_payment': False
    }
    return render(request, 'payments/payments.html', context)


@skip_if_disabled
@never_cache
def confirmation(request, status, recurring=False):
    context = {
        'status': status,
        'recurring': recurring
    }
    return render(request, 'payments/thank_you.html', context)


@skip_if_disabled
@never_cache
@csrf_exempt
def contribute_recurring_payment_initial(request):
    initial_data = {}
    if request.user.is_authenticated and request.user.email:
        initial_data = {
            'name': request.user.fullname,
            'email': request.user.email,
        }

    form = RecurringPaymentForm(initial=initial_data)

    context = {
        'form': form,
        'hide_cta': True,
        'recurring_payment': True
    }
    return render(request, 'payments/payments.html', context)


@skip_if_disabled
@login_required
@never_cache
@csrf_exempt
def contribute_recurring_payment_subscription(request):
    initial_data = {}
    if request.GET:
        initial_data = {
            k: v for k, v in request.GET.iteritems() if k in RecurringPaymentForm().fields.keys()
        }
    elif request.user.is_authenticated and request.user.email:
        initial_data = {
            'name': request.user.fullname,
            'email': request.user.email,
        }

    if request.POST:
        form = RecurringPaymentForm(request.POST)
        if form.is_valid():
            if form.make_recurring_payment_charge(request.user):
                if settings.MDN_CONTRIBUTION_CONFIRMATION_EMAIL:
                    payments_thank_you_email.delay(
                        form.cleaned_data['name'],
                        form.cleaned_data['email'],
                        recurring=True
                    )
                return redirect('recurring_payment_succeeded')
            return redirect('recurring_payment_error')

        form = RecurringPaymentForm(request.POST)
    else:
        form = RecurringPaymentForm(initial=initial_data)

    context = {
        'form': form,
        'hide_cta': True,
        'recurring_payment': True
    }
    return render(request, 'payments/payments.html', context)


@skip_if_disabled
@never_cache
def payment_terms(request):
    return render(request, 'payments/terms.html')


@skip_if_disabled
@login_required
@never_cache
def recurring_payment_management(request):
    context = {
        'support_mail_link': 'mailto:' + settings.CONTRIBUTION_SUPPORT_EMAIL + '?Subject=Recurring%20payment%20support',
        'support_mail': settings.CONTRIBUTION_SUPPORT_EMAIL,
        'cancel_request': False,
        'cancel_success': False,
    }

    if request.user.stripe_customer_id and 'stripe_cancel_subscription' in request.POST:
        cancel_success = cancel_stripe_customer_subscription(
            request.user.stripe_customer_id,
            request.user.email,
            request.user.username
        )
        context['cancel_request'] = True
        context['cancel_success'] = cancel_success

    if request.user.stripe_customer_id:
        context.update(
            get_stripe_customer_data(
                request.user.stripe_customer_id,
                request.user.email,
                request.user.username
            ),
        )

    return render(request, 'payments/management.html', context)
