# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from functools import wraps

from django.conf import settings
from django.http import Http404
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from stripe.error import StripeError

from kuma.core.decorators import login_required

from .utils import (cancel_stripe_customer_subscription,
                    enabled,
                    get_stripe_customer_data)

log = logging.getLogger('kuma.payments.views')


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
def contribute(request):
    return render(request, 'payments/payments.html')


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
        context['cancel_request'] = True
        cancel_success = False
        try:
            cancel_stripe_customer_subscription(request.user.stripe_customer_id)
        except StripeError:
            log.exception(
                'Stripe subscription cancellation: Stripe error for %s [%s]',
                request.user.username, request.user.email)
        else:
            cancel_success = True
        context['cancel_success'] = cancel_success

    if request.user.stripe_customer_id:
        data = {
            'active_subscriptions': False
        }
        try:
            data = get_stripe_customer_data(request.user.stripe_customer_id)
        except StripeError:
            log.exception(
                'Stripe subscription data: Stripe error for %s [%s]',
                request.user.username, request.user.email)
        context.update(data)

    return render(request, 'payments/management.html', context)
