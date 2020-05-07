import csv
from io import StringIO

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


from kuma.users import sendinblue
from kuma.users.models import User, UserSubscription


class Command(BaseCommand):
    help = "Exports newsletter subscribed users to sendinblue"

    def handle(self):
        if not settings.SENDINBLUE_API_KEY:
            raise CommandError("SENDINBLUE_API_KEY config not set")

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
            row = {
                "EMAIL": user.email,
                "FIRSTNAME": user.first_name,
                "LASTNAME": user.last_name,
            }
            if is_paying:
                paying_users.append(row)
            else:
                non_paying_users.append(row)

        def export_users(users, list_id):
            print(f"Exporting {len(users):,} on list {list_id}")
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

            response = sendinblue.request("POST", "contacts/import", json=payload)
            response.raise_for_status()

        export_users(paying_users, settings.SENDINBLUE_PAYING_LIST_ID)
        export_users(non_paying_users, settings.SENDINBLUE_NOT_PAYING_LIST_ID)
