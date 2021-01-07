# Generated by Django 2.2.16 on 2021-01-07 13:38

from django.db import migrations


def forward(apps, schema_editor):
    Flag = apps.get_model("waffle", "Flag")
    Flag.objects.filter(name__in=["kumaediting", "page_move", "section_edit"]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("wiki", "0009_auto_20210105_0406"),
    ]

    operations = []
