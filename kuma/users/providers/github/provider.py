from allauth.account.models import EmailAddress
from allauth.socialaccount import providers
from allauth.socialaccount.providers.github.provider import (GitHubProvider,
                                                             GitHubAccount)


class KumaGitHubAccount(GitHubAccount):
    """
    A custom account object to have some extra helpers.
    """
    def get_email_addresses(self):
        return self.account.extra_data.get('email_addresses')


class KumaGitHubProvider(GitHubProvider):
    """
    A custom Github provider that addtionally is able to handle the
    list of email addresses fetched from the GitHub API and use it
    to populate the list of verified email addresses with it.

    It'll use the "user:email" OAuth2 scope to be able to fetch the
    private email addresses from users.
    """
    package = 'kuma.users.providers.github'
    account_class = KumaGitHubAccount

    def extract_email_addresses(self, data):
        email_addresses = []
        print data
        for email_address in data.get('email_addresses', []):
            # let's ignore all email address that have not been verified at
            # Github's side
            if not email_address.get('verified', False):
                continue
            email_addresses.append(EmailAddress(email=email_address['email'],
                                                verified=True,
                                                primary=email_address['primary']))
        return email_addresses

    def get_default_scope(self):
        return ['user:email']

providers.registry.register(KumaGitHubProvider)
