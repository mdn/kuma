import csv
from io import StringIO

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from kuma.users.models import User, UserSubscription
from kuma.users.newsletter import sendinblue


class Command(BaseCommand):
    help = "Exports newsletter subscribed users to sendinblue"

    def handle(self, **options):
        if not settings.SENDINBLUE_API_KEY:
            raise CommandError("SENDINBLUE_API_KEY config not set")

        active_subscriber_user_ids = set(
            UserSubscription.objects.filter(canceled__isnull=True).values_list(
                "user_id", flat=True
            )
        )
        users = User.objects.filter(is_newsletter_subscribed=True).exclude(email="")

        csv_out = StringIO()
        writer = csv.DictWriter(
            csv_out,
            fieldnames=["EMAIL", "USERNAME", "IS_PAYING"],
        )
        writer.writeheader()
        for user in users.only("id", "email"):
            writer.writerow(
                {
                    "EMAIL": user.email,
                    "USERNAME": user.username,
                    "IS_PAYING": "Yes"
                    if user.id in active_subscriber_user_ids
                    else "No",
                }
            )

        payload = {
            "fileBody": csv_out.getvalue(),
            "listIds": [int(settings.SENDINBLUE_LIST_ID)],
            "updateExistingContacts": True,
            "emptyContactsAttributes": True,
        }

        print(f"Exporting {len(users):,} users")

        response = sendinblue.request("POST", "contacts/import", json=payload)
        response.raise_for_status()
