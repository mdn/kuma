from kuma.users.models import UserProfile

# Finds union of valid subscription id's from input and UserProfile.SubscriptionType.values
# Should only be mdn_plus + one of 'SubscriptionType.values'
def get_valid_subscription_type_or_none(input):
    subscription_types = list(set(input) & set(UserProfile.SubscriptionType.values))
    if len(subscription_types) > 1:
        print("Multiple subscriptions found in update %s" % subscription_types)
        #Sort array lexicographically. At least makes wrong answer consistent. 
        subscription_types.sort()

    return subscription_types[0] if len(subscription_types) > 0 else ""
