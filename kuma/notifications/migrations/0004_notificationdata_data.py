# Generated by Django 3.2.7 on 2021-12-13 15:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("notifications", "0003_watch_title"),
    ]

    operations = [
        migrations.AddField(
            model_name="notificationdata",
            name="data",
            field=models.JSONField(default="{}"),
        ),
    ]