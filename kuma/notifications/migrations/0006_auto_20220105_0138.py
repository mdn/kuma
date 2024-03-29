# Generated by Django 3.2.7 on 2022-01-05 01:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("notifications", "0005_auto_20211215_2004"),
    ]

    operations = [
        migrations.AddField(
            model_name="userwatch",
            name="browser_compatibility",
            field=models.JSONField(default=list),
        ),
        migrations.AddField(
            model_name="userwatch",
            name="content_updates",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="userwatch",
            name="custom",
            field=models.BooleanField(default=False),
        ),
    ]
