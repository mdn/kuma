# Generated by Django 3.2.7 on 2022-01-18 12:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("notifications", "0008_default_watch"),
    ]

    operations = [
        migrations.AddField(
            model_name="notificationdata",
            name="page_url",
            field=models.TextField(default="/"),
            preserve_default=False,
        ),
    ]
