# Generated by Django 3.2.7 on 2021-09-22 11:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="userprofile",
            name="is_subscriber",
        ),
        migrations.RemoveField(
            model_name="userprofile",
            name="subscriber_number",
        ),
        migrations.AddField(
            model_name="userprofile",
            name="fxa_uid",
            field=models.CharField(blank=True, max_length=255, null=True, unique=True),
        ),
    ]
