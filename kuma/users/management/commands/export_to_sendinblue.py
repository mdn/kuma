import csv
from io import StringIO

from django.core.management.base import BaseCommand

from kuma.core.utils import requests_retry_session
from kuma.users.models import User, UserSubscription

URL = "https://api.sendinblue.com/v3/contacts/import"


class Command(BaseCommand):
    help = "Exports newsletter subscribed users to sendinblue"

    def add_arguments(self, parser):
        parser.add_argument("--api-key")
        parser.add_argument("--paying-users-list-id", type=int)
        parser.add_argument("--non-paying-users-list-id", type=int)

    def handle(self, **options):
        active_subscriber_user_ids = set(
            UserSubscription.objects.filter(canceled__isnull=True).values_list(
                "user_id", flat=True
            )
        )
        users = User.objects.filter(is_newsletter_subscribed=True).exclude(email="")
        paying_users = []
        non_paying_users = []
        for user in users.only("email", "first_name", "last_name"):
            is_paying = user.id in active_subscriber_user_ids
            list = paying_users if is_paying else non_paying_users
            list.append(
                {
                    "EMAIL": user.email,
                    "FIRSTNAME": user.first_name,
                    "LASTNAME": user.last_name,
                }
            )

        def export_users(users, list_id):
            csv_out = StringIO()
            writer = csv.DictWriter(
                csv_out, fieldnames=["EMAIL", "FIRSTNAME", "LASTNAME"]
            )
            writer.writeheader()
            for user in users:
                writer.writerow(user)

            payload = {
                "fileBody": csv_out.getvalue(),
                "listIds": [list_id],
                "updateExistingContacts": True,
                "emptyContactsAttributes": True,
            }
            headers = {
                "api-key": options["api_key"],
                "accept": "application/json",
                "content-type": "application/json",
            }

            response = requests_retry_session().request("POST", URL, json=payload, headers=headers)
            response.raise_for_status()

        print(f"Exporting {len(paying_users)} paying user(s)")
        export_users(paying_users, options["paying_users_list_id"])
        print(f"Exporting {len(non_paying_users)} non-paying users")
        export_users(non_paying_users, options["non_paying_users_list_id"])
