# Generated by Django 3.2.5 on 2021-07-12 19:04

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("documenturls", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Bookmark",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("notes", models.JSONField(default=list)),
                ("deleted", models.DateTimeField(null=True)),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("modified", models.DateTimeField(auto_now=True)),
                (
                    "documenturl",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="documenturls.documenturl",
                        verbose_name="Document URL",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Bookmark",
                "unique_together": {("documenturl", "user_id")},
            },
        ),
    ]
