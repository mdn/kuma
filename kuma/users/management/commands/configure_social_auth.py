import fileinput
import os
import sys

from allauth.socialaccount.models import SocialApp
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand

LOCALHOST = "localhost.org:8000"
DOMAIN = "localhost.org"

OVERWRITE_PROMPT = (
    'There\'s already a SocialApp for %s, if you want to overwrite it type "yes":'
)
GITHUB_INFO = (
    'Visit https://github.com/settings/developers and click "New OAuth App"\n'
    'Set "Homepage URL" to "http://localhost.org:8000/" and Authorization callback URL to '
    + '"http://localhost.org:8000/users/github/login/callback/" respectively'
)
GOOGLE_INFO = (
    "Visit https://console.developers.google.com/projectcreate and create a new project\n"
    "After that visit https://console.developers.google.com/apis/credentials and add the following URLs:\n"
    "Authorized JavaScript origins: http://localhost.org:8000\n"
    "Authorized redirect URIs: http://localhost.org:8000/users/google/login/callback/\n"
)
ENV_INFO = "Putting SITE_ID and DOMAIN into .env"
HOSTS_INFO = (
    'You should should run "docker-compose stop; docker-compose up" now, so that the .env updates are applied\n.'
    "Make sure your hosts file contains these lines:\n"
    "127.0.0.1 localhost demos localhost.org wiki.localhost.org\n"
    "::1             localhost.org wiki.localhost.org"
)


def overwrite_or_create_env_vars(env_vars):
    file_path = os.path.join(os.getcwd(), ".env")

    for line in fileinput.input(file_path, inplace=True):
        key = line.strip().split("=")[0]
        if key not in env_vars:
            sys.stdout.write(line)

    with open(file_path, "a") as file:
        file.write("\n")
        for key, value in env_vars.items():
            file.write(key + "=" + str(value) + "\n")


class Command(BaseCommand):
    help = "Configure Kuma for Sign-In with GitHub and Google"

    def handle(self, **options):
        print("\n")

        social_apps = []
        for provider in ["github", "google"]:
            social_app = SocialApp.objects.filter(provider=provider).first()
            if social_app is None or input(OVERWRITE_PROMPT % provider) == "yes":
                print("\n")

                print(GITHUB_INFO if provider == "github" else GOOGLE_INFO)

                # TODO: changes this back to the walrus operator once pfylakes supports it
                # related issue: https://github.com/PyCQA/pyflakes/pull/457
                client_id = ""
                while not client_id:
                    client_id = input("Client ID:").strip()
                    pass
                client_secret = ""
                while not client_secret:
                    client_secret = input("Client Secret:").strip()
                    pass

                social_app, created = SocialApp.objects.update_or_create(
                    provider=provider,
                    defaults={
                        "name": "MDN Development",
                        "client_id": client_id,
                        "secret": client_secret,
                    },
                )

            social_apps.append(social_app)

        site, created = Site.objects.update_or_create(
            domain=LOCALHOST, defaults={"name": LOCALHOST}
        )
        for social_app in social_apps:
            social_app.sites.add(site)

        print("\n")

        print(ENV_INFO)
        overwrite_or_create_env_vars(
            {"SITE_ID": site.id, "DOMAIN": DOMAIN}
            if site.id != settings.SITE_ID
            else {"DOMAIN": DOMAIN}
        )

        print(HOSTS_INFO)
