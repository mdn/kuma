import requests_mock
from allauth.account.models import EmailAddress
from allauth.socialaccount.providers import registry
from allauth.socialaccount.providers.github.views import GitHubOAuth2Adapter
from allauth.socialaccount.models import SocialApp
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.utils.crypto import get_random_string
from django.utils.six.moves.urllib_parse import urlparse, parse_qs

from kuma.core.tests import KumaTestCase
from kuma.core.urlresolvers import reverse
from kuma.wiki.tests import revision as create_revision, document as create_document
from ..providers.github.provider import KumaGitHubProvider


class UserTestMixin(object):
    """Base TestCase for the users app test cases."""
    fixtures = ['test_users.json']

    def setUp(self):
        super(UserTestMixin, self).setUp()
        self.user_model = get_user_model()


class UserTestCase(UserTestMixin, KumaTestCase):
    pass


def user(save=False, **kwargs):
    if 'username' not in kwargs:
        kwargs['username'] = get_random_string(length=15)
    password = kwargs.pop('password', 'password')
    groups = kwargs.pop('groups', [])
    user = get_user_model()(**kwargs)
    user.set_password(password)
    if save:
        user.save()
    if groups:
        user.groups = groups
    return user


def email(save=False, **kwargs):
    if 'user' not in kwargs:
        kwargs['user'] = user(save=True)
    if 'email' not in kwargs:
        kwargs['email'] = '%s@%s.com' % (get_random_string(),
                                         get_random_string())
    email = EmailAddress(**kwargs)
    if save:
        email.save()
    return email


class SampleRevisionsMixin(object):
    """Mixin with an original revision and a method to create more revisions."""
    def setUp(self):
        super(SampleRevisionsMixin, self).setUp()

        # Some users to use in the tests
        self.testuser = self.user_model.objects.get(username='testuser')
        self.testuser2 = self.user_model.objects.get(username='testuser2')
        self.admin = self.user_model.objects.get(username='admin')

        # Create an original revision on a document by the admin user
        self.document = create_document(save=True)
        self.original_revision = create_revision(
            title='Revision 0',
            document=self.document,
            creator=self.admin,
            save=True)

    def create_revisions(self, num, creator, document=None):
        """Create as many revisions as requested, and return a list of them."""
        # If document is None, then we create a new document for each revision
        create_new_documents = not document
        revisions_created = []
        for i in range(1, 1 + num):
            if create_new_documents is True:
                document = create_document(save=True)
            new_revision = create_revision(
                title='Doc id {} Revision {}'.format(document.id, i),
                document=document,
                creator=creator,
                save=True)
            revisions_created.append(new_revision)
        return revisions_created


class SocialTestMixin(object):
    github_token_data = {
        'uid': 1,
        'access_token': 'github_token',
    }
    github_profile_data = {
        'login': 'octocat',
        'id': 1,
        'email': 'octocat@example.com',
        # Unused profile items
        'avatar_url': 'https://github.com/images/error/octocat_happy.gif',
        'gravatar_id': 'somehexcode',
        'url': 'https://api.github.com/users/octocat',
        'html_url': 'https://github.com/octocat',
        'followers_url': 'https://api.github.com/users/octocat/followers',
        'following_url': 'https://api.github.com/users/octocat/following{/other_user}',
        'gists_url': 'https://api.github.com/users/octocat/gists{/gist_id}',
        'starred_url': 'https://api.github.com/users/octocat/starred{/owner}{/repo}',
        'subscriptions_url': 'https://api.github.com/users/octocat/subscriptions',
        'organizations_url': 'https://api.github.com/users/octocat/orgs',
        'repos_url': 'https://api.github.com/users/octocat/repos',
        'events_url': 'https://api.github.com/users/octocat/events{/privacy}',
        'received_events_url': 'https://api.github.com/users/octocat/received_events',
        'type': 'User',
        'site_admin': False,
        'name': 'monalisa octocat',
        'company': 'GitHub',
        'blog': 'https://github.com/blog',
        'location': 'San Francisco',
        'hireable': False,
        'public_repos': 2,
        'public_gists': 1,
        'followers': 20,
        'following': 0,
        'created_at': '2008-01-14T04:33:35Z',
        'updated_at': '2008-01-14T04:33:35Z'
    }
    github_email_data = [
        {
            'email': 'octocat-private@example.com',
            'verified': True,
            'primary': True,
            # Added Feb 2017, bug 1339375
            'visibility': 'private'
        }
    ]

    def github_login(
            self, token_data=None, profile_data=None, email_data=None,
            process='login'):
        """
        Mock a login to GitHub and return the response.

        Keyword Arguments:
        token_data - OAuth token data, or None for default
        profile_data - GitHub profile data, or None for default
        email_data - GitHub email data, or None for default
        process - 'login', 'connect', or 'redirect'
        """
        login_url = reverse('github_login',
                            locale=settings.WIKI_DEFAULT_LANGUAGE)
        callback_url = reverse('github_callback', unprefixed=True)

        # Ensure GitHub is setup as an auth provider
        self.ensure_github_app()

        # Start the login process
        # Store state in the session, and redirect the user to GitHub
        login_response = self.client.get(login_url, {'process': process})
        assert login_response.status_code == 302
        location = urlparse(login_response['location'])
        query = parse_qs(location.query)
        assert callback_url in query['redirect_uri'][0]
        state = query['state'][0]

        # Callback from GitHub, mock follow-on GitHub responses
        with requests_mock.Mocker() as mock_requests:
            # The callback view will make requests back to Github:
            # The OAuth2 authentication token (or error)
            mock_requests.post(
                GitHubOAuth2Adapter.access_token_url,
                json=token_data or self.github_token_data,
                headers={'content-type': 'application/json'})
            # The authenticated user's profile data
            mock_requests.get(
                GitHubOAuth2Adapter.profile_url,
                json=profile_data or self.github_profile_data)
            # The user's emails, which could be an empty list
            if email_data is None:
                email_data = self.github_email_data
            mock_requests.get(GitHubOAuth2Adapter.emails_url, json=email_data)

            # Simulate the callback from Github
            data = {'code': 'github_code', 'state': state}
            response = self.client.get(callback_url, data, follow=True)

        return response

    def ensure_github_app(self):
        """Ensure a GitHub SocialApp is installed, configured."""
        provider = registry.by_id(KumaGitHubProvider.id)
        app, created = SocialApp.objects.get_or_create(
            provider=provider.id,
            defaults={
                'name': provider.id,
                'client_id': 'app123id',
                'key': provider.id,
                'secret': 'dummy'})
        if created:
            app.sites.add(Site.objects.get_current())
        return app
