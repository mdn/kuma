from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Converts specified user into a superuser"

    def add_arguments(self, parser):
        parser.add_argument(
            "username", nargs=1, help="Username address for account to admin-ize."
        )

        parser.add_argument("--password", default=False, help="Password of the user")

    def handle(self, *args, **options):
        username = options["username"][0]
        password = options["password"]
        User = get_user_model()

        try:
            user = User.objects.get(username=username)

        except User.DoesNotExist:
            raise CommandError("User %s does not exist." % username)

        if user.is_superuser and user.is_staff and not password:
            raise CommandError("User already has the power!")

        if password:
            user.set_password(password)

        user.is_superuser = True
        user.is_staff = True
        user.save()
        self.stdout.write("Done!")
