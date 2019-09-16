import fileinput, os, sys, urllib2

from django.core.management.base import BaseCommand, CommandError
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp

LOCALHOST = 'localhost:8000'
MDN_LOCALHOST = 'mdn.localhost'

OVERWRITE_PROMPT = 'There\'s already a SocialApp for GitHub, if you want to overwrite it type "yes":'
GITHUB_INFO = '\n'.join([
    'Visit https://github.com/settings/developers and click "New OAuth App"',
    'Set "Homepage URL" to "http://mdn.localhost:8000/" and Authorization callback URL to ' +
    '"http://mdn.localhost:8000/users/github/login/callback/" respectively'
])
ENV_INFO = 'Putting SITE_ID and DOMAIN into .env'
HOSTS_INFO = '\n'.join([
    'Make sure your hosts file contains these lines:'
    '127.0.0.1 kubernetes.docker.internal localhost demos mdn.localhost beta.mdn.localhost wiki.mdn.localhost',
    '::1             mdn.localhost beta.mdn.localhost wiki.mdn.localhost'
])


def overwrite_or_create_env_vars(env_vars):
    file_path = os.path.join(os.getcwd(), '.env')

    for line in fileinput.input(file_path, inplace=True):
        key = line.strip().split('=')[0]
        if key not in env_vars:
            sys.stdout.write(line)

    with open(file_path, 'a') as file:
        for key, value in env_vars.iteritems():
            file.write('\n' + key + '=' + str(value))


class Command(BaseCommand):
    help = 'Configure Kuma for Sign-In with GitHub'

    def handle(self, **options):
        print('\n')

        social_app = SocialApp.objects.filter(provider='github').first()
        if social_app is not None and raw_input(OVERWRITE_PROMPT) == 'yes':
            print('\n')

            print(GITHUB_INFO)
            client_id = raw_input('Client ID: ').strip()
            client_secret = raw_input('Client Secret: ').strip()

            social_app, created = SocialApp.objects.update_or_create(
                provider='github',
                defaults={
                    'name': 'MDN Development',
                    'client_id': client_id,
                    'secret': client_secret
                }
            )

        site, created = Site.objects.update_or_create(
            domain=LOCALHOST,
            defaults={'name': LOCALHOST}
        )
        social_app.sites.add(site)

        print('\n')

        print(ENV_INFO)
        overwrite_or_create_env_vars({'SITE_ID': site.id, 'DOMAIN': MDN_LOCALHOST})

        print(HOSTS_INFO)
