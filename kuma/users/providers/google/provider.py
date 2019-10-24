from allauth.account.models import EmailAddress
from allauth.socialaccount.providers.google.provider import (GoogleAccount,
                                                             GoogleProvider)


class KumaGoogleProvider(GoogleProvider):
    id = 'google'
    package = 'kuma.users.providers.google'
    account_class = GoogleAccount


provider_classes = [KumaGoogleProvider]
