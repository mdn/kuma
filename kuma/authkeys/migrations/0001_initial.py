from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("contenttypes", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Key",
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
                (
                    "key",
                    models.CharField(
                        verbose_name="Lookup key",
                        max_length=64,
                        editable=False,
                        db_index=True,
                    ),
                ),
                (
                    "hashed_secret",
                    models.CharField(
                        verbose_name="Hashed secret", max_length=128, editable=False
                    ),
                ),
                (
                    "description",
                    models.TextField(verbose_name="Description of intended use"),
                ),
                ("created", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        editable=False,
                        to=settings.AUTH_USER_MODEL,
                        on_delete=models.PROTECT,
                    ),
                ),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="KeyAction",
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
                ("action", models.CharField(max_length=128)),
                ("notes", models.TextField(null=True)),
                ("object_id", models.PositiveIntegerField()),
                ("created", models.DateTimeField(auto_now_add=True)),
                (
                    "content_type",
                    models.ForeignKey(
                        to="contenttypes.ContentType", on_delete=models.CASCADE
                    ),
                ),
                (
                    "key",
                    models.ForeignKey(
                        related_name="history",
                        to="authkeys.Key",
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={},
            bases=(models.Model,),
        ),
    ]
