from allauth.account.models import EmailAddress
from allauth.socialaccount.providers.github.provider import (
    GitHubAccount,
    GitHubProvider,
)


class KumaGitHubAccount(GitHubAccount):
    """
    A custom account object to have some extra helpers.
    """

    def get_email_addresses(self):
        return self.account.extra_data.get("email_addresses")

    def to_str(self):
        dflt = super(KumaGitHubAccount, self).to_str()
        return self.account.extra_data.get("login", dflt)


class KumaGitHubProvider(GitHubProvider):
    """
    A custom GitHub provider that additionally is able to handle the
    list of email addresses fetched from the GitHub API and use it
    to populate the list of verified email addresses with it.

    It'll use the "user:email" OAuth2 scope to be able to fetch the
    private email addresses from users.
    """

    id = "github"
    package = "kuma.users.providers.github"
    account_class = KumaGitHubAccount

    def extract_email_addresses(self, data):
        result = []
        for email_address in data.get("email_addresses", ()):
            # Ignore all email addresses that have not been verified by GitHub.
            email = email_address.get("email", "").strip()
            if email and email_address.get("verified"):
                result.append(
                    EmailAddress(
                        email=email, verified=True, primary=email_address["primary"]
                    )
                )
        return result


provider_classes = [KumaGitHubProvider]
