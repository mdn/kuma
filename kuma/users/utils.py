from datetime import datetime

import stripe
from django.conf import settings


def retrieve_stripe_subscription(customer):
    for subscription in customer.subscriptions.list().auto_paging_iter():
        # We have to use array indexing syntax, as stripe uses dicts to
        # represent its objects (dicts come with an .items method)
        for item in subscription["items"].auto_paging_iter():
            if item.plan.id == settings.STRIPE_PLAN_ID:
                return subscription

    return None


def create_stripe_customer_and_subscription_for_user(user, email, stripe_token):
    customer = (
        stripe.Customer.retrieve(user.stripe_customer_id)
        if user.stripe_customer_id
        else None
    )
    if not customer or customer.email != email:
        customer = stripe.Customer.create(email=email, source=stripe_token,)
        user.stripe_customer_id = customer.id
        user.save()

    if retrieve_stripe_subscription(customer) is None:
        stripe.Subscription.create(
            customer=customer.id, items=[{"plan": settings.STRIPE_PLAN_ID}],
        )


def retrieve_stripe_subscription_info(user):
    stripe_customer = (
        stripe.Customer.retrieve(user.stripe_customer_id, expand=["default_source"],)
        if settings.STRIPE_PLAN_ID and user.stripe_customer_id
        else None
    )

    stripe_subscription = (
        retrieve_stripe_subscription(stripe_customer)
        if stripe_customer and stripe_customer.email == user.email
        else None
    )
    if stripe_subscription:
        source = stripe_customer.default_source
        if source.object == "card":
            card = source
        elif source.object == "source":
            card = source.card
        else:
            raise ValueError(
                f"unexpected stripe customer default_source of type {source.object!r}"
            )

        return {
            "next_payment_at": datetime.fromtimestamp(
                stripe_subscription.current_period_end
            ),
            "brand": card.brand,
            "expires_at": f"{card.exp_month}/{card.exp_year}",
            "last4": card.last4,
            "zip": card.address_zip,
        }

    return None
