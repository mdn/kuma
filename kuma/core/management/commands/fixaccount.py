from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount


class Command(BaseCommand):
    help = 'Reconnects an MDN account (Persona) to an email address'

    def add_arguments(self, parser):
        parser.add_argument('username', nargs=1,
                            help='MDN account username.')
        parser.add_argument('email', nargs=1,
                            help='Email address to connect.')

    def handle(self, *args, **options):
        username = options['username'][0]
        email = options['email'][0]

        User = get_user_model()

        try:
            user = User.objects.get(username=username)

        except User.DoesNotExist:
            raise CommandError('User %s does not exist.' % username)

        if user.email != email:
            self.stdout.write('Fixing email address in auth_user record.')
            user.email = email
            user.save()

        # Fix the django-allauth EmailAddress record
        try:
            emailaddress = EmailAddress.objects.get(user=user)
        except EmailAddress.DoesNotExist:
            raise CommandError(
                'There is no account_emailaddress record for this account '
                'which suggests it was created with createsuperuser. Please '
                'log into the account with Persona and go through the signup '
                'process.'
            )

        if emailaddress.email != email:
            self.stdout.write('Fixing email address in account_emailaddress '
                              'record.')
            emailaddress.change(None, email, confirm=False)
            emailaddress.verified = True
            emailaddress.save()

        try:
            SocialAccount.objects.get(user=user)
        except SocialAccount.DoesNotExist:
            self.stdout.write('Creating a socialaccount_socialaccount record.')
            SocialAccount.objects.create(user=user, provider='Persona', uid=email)

        self.stdout.write('Done!')
