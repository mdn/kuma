import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY
stripe.max_network_retries = 5

stripe = stripe


def retrieve_stripe_subscription(customer):
    for subscription in customer.subscriptions.list().auto_paging_iter():
        # We have to use array indexing syntax, as stripe uses dicts to
        # represent its objects (dicts come with an .items method)
        for item in subscription['items'].auto_paging_iter():
            if item.plan.id == settings.STRIPE_PLAN_ID:
                return subscription

    return None
