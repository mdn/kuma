import csv
import json
from io import StringIO

import requests
from django.core.management.base import BaseCommand
from django.db import connection

URL = "https://api.sendinblue.com/v3/contacts/import"


def _dictfetchall(cursor):
    "Returns all rows from a cursor as a dict. source: https://stackoverflow.com/a/14294314"
    desc = cursor.description
    return [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()]


class Command(BaseCommand):
    help = "Exports newsletter subscribed users to sendinblue"

    def add_arguments(self, parser):
        parser.add_argument("--api-key")
        parser.add_argument("--paying-users-list-id", type=int)
        parser.add_argument("--non-paying-users-list-id", type=int)

    def handle(self, **options):
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT
                email,
                first_name,
                last_name,
                EXISTS(
                    SELECT 1
                    FROM users_usersubscription
                    WHERE user_id = auth_user.id AND canceled IS NULL
                ) AS is_paying
            FROM auth_user
            WHERE email <> '' AND is_newsletter_subscribed
        """
        )
        rows = _dictfetchall(cursor)

        paying_users = []
        non_paying_users = []
        for row in rows:
            if row["is_paying"]:
                paying_users.append(row)
            else:
                non_paying_users.append(row)

        def export_users(users, list_id):
            csv_out = StringIO()
            writer = csv.DictWriter(
                csv_out, fieldnames=["EMAIL", "FIRSTNAME", "LASTNAME"]
            )
            writer.writeheader()
            for user in users:
                writer.writerow(
                    {
                        "EMAIL": user["email"],
                        "FIRSTNAME": user["first_name"],
                        "LASTNAME": user["last_name"],
                    }
                )

            payload = json.dumps(
                {
                    "fileBody": csv_out.getvalue(),
                    "listIds": [list_id],
                    "updateExistingContacts": True,
                    "emptyContactsAttributes": True,
                },
                separators=(",", ":"),
            )
            headers = {
                "api-key": options["api_key"],
                "accept": "application/json",
                "content-type": "application/json",
            }

            response = requests.request("POST", URL, data=payload, headers=headers)
            response.raise_for_status()

        print(f"Exporting {len(paying_users)} paying user(s)")
        export_users(paying_users, options["paying_users_list_id"])
        print(f"Exporting {len(non_paying_users)} non-paying user(s)")
        export_users(non_paying_users, options["non_paying_users_list_id"])
