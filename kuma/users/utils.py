from django.conf import settings


def retrieve_stripe_subscription(customer):
    for subscription in customer.subscriptions.list().auto_paging_iter():
        # We have to use array indexing syntax, as stripe uses dicts to
        # represent its objects (dicts come with an .items method)
        for item in subscription['items'].auto_paging_iter():
            if item.plan.id == settings.STRIPE_PLAN_ID:
                return subscription

    return None
