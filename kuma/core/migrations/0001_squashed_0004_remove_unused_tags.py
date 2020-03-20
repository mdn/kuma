import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("taggit", "0002_auto_20150616_2121"),
    ]

    operations = [
        migrations.CreateModel(
            name="IPBan",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ("ip", models.GenericIPAddressField()),
                (
                    "created",
                    models.DateTimeField(
                        default=django.utils.timezone.now, db_index=True
                    ),
                ),
                ("deleted", models.DateTimeField(null=True, blank=True)),
            ],
        ),
    ]
