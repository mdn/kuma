from datetime import datetime

import stripe
from django.conf import settings

from kuma.users.models import User

# TODO: How to make this user have a name that can't collide with real users?
TEST_USER_USERNAME = 'this_should_be_something_real_users_cant_have'


def get_stripe_test_user(fresh=False):
    if fresh:
        User.objects.filter(username=TEST_USER_USERNAME).delete()
    user, _ = User.objects.get_or_create(
        email='payer@example.com',
        username=TEST_USER_USERNAME,
        is_staff=True
    )
    user.set_unusable_password()
    user.save()
    return user


def get_stripe_config(test_mode=False):
    if test_mode:
        return settings.STRIPE_SECRET_KEY, settings.STRIPE_PLAN_ID
    else:
        return settings.STRIPE_TEST_SECRET_KEY, settings.STRIPE_TEST_PLAN_ID


def retrieve_stripe_subscription(customer):
    for subscription in customer.subscriptions.list().auto_paging_iter():
        # We have to use array indexing syntax, as stripe uses dicts to
        # represent its objects (dicts come with an .items method)
        for item in subscription['items'].auto_paging_iter():
            if item.plan.id == settings.STRIPE_PLAN_ID:
                return subscription

    return None


def create_stripe_customer_and_subscription_for_user(user, email, stripe_token, test_mode=False):
    api_key, plan_id = get_stripe_config(test_mode)
    customer = stripe.Customer.retrieve(user.stripe_customer_id) if user.stripe_customer_id else None
    if not customer or customer.email != email:
        customer = stripe.Customer.create(
            email=email,
            source=stripe_token,
            api_key=api_key
        )
        user.stripe_customer_id = customer.id
        user.save()

    if retrieve_stripe_subscription(customer) is None:
        stripe.Subscription.create(
            customer=customer.id,
            items=[{
                'plan': plan_id,
            }],
            api_key=api_key
        )


def retrieve_stripe_subscription_info(user, test_mode):
    api_key, plan_id = get_stripe_config(test_mode)

    stripe_customer = stripe.Customer.retrieve(
        user.stripe_customer_id,
        expand=['default_source'],
        api_key=api_key
    ) if plan_id and user.stripe_customer_id else None

    stripe_subscription = (
        retrieve_stripe_subscription(stripe_customer)
        if stripe_customer and stripe_customer.email == user.email
        else None
    )
    if stripe_subscription:
        source = stripe_customer.default_source
        return {
            'next_payment_at': datetime.fromtimestamp(stripe_subscription.current_period_end),
            'brand': source.brand,
            'expires_at': f'{source.exp_month}/{source.exp_year}',
            'last4': source.last4,
            'zip': source.address_zip
        }

    return None
