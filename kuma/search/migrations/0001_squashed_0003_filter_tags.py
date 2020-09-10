import django.utils.timezone
import taggit.managers
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("taggit", "0001_initial"),
        ("contenttypes", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Filter",
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
                    "name",
                    models.CharField(
                        help_text=b"the English name of the filter to be shown in the frontend UI",
                        max_length=255,
                        db_index=True,
                    ),
                ),
                (
                    "slug",
                    models.CharField(
                        help_text=b"the slug to be used as a query parameter in the search URL",
                        max_length=255,
                        db_index=True,
                    ),
                ),
                (
                    "shortcut",
                    models.CharField(
                        help_text=b"the name of the shortcut to show in the command and query UI. e.g. fxos",
                        max_length=255,
                        null=True,
                        db_index=True,
                        blank=True,
                    ),
                ),
                (
                    "operator",
                    models.CharField(
                        default=b"OR",
                        help_text=b"The logical operator to use if more than one tag is given",
                        max_length=3,
                        choices=[(b"OR", b"OR"), (b"AND", b"AND")],
                    ),
                ),
                (
                    "enabled",
                    models.BooleanField(
                        default=True,
                        help_text=b"Whether this filter is shown to users or not.",
                    ),
                ),
                (
                    "visible",
                    models.BooleanField(
                        default=True,
                        help_text=b"Whether this filter is shown at public places, e.g. the command and query UI",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="FilterGroup",
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
                ("name", models.CharField(max_length=255)),
                (
                    "slug",
                    models.CharField(
                        help_text=b"the slug to be used as the name of the query parameter in the search URL",
                        max_length=255,
                        null=True,
                        blank=True,
                    ),
                ),
                (
                    "order",
                    models.IntegerField(
                        default=1,
                        help_text=b"An integer defining which order the filter group should show up in the sidebar",
                    ),
                ),
            ],
            options={"ordering": ("-order", "name")},
        ),
        migrations.CreateModel(
            name="Index",
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
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "name",
                    models.CharField(
                        help_text=b"The search index name, set to the created date when left empty",
                        max_length=30,
                        null=True,
                        blank=True,
                    ),
                ),
                ("promoted", models.BooleanField(default=False)),
                ("populated", models.BooleanField(default=False)),
            ],
            options={
                "ordering": ["-created_at"],
                "verbose_name": "Index",
                "verbose_name_plural": "Indexes",
            },
        ),
        migrations.CreateModel(
            name="OutdatedObject",
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
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("object_id", models.PositiveIntegerField()),
                (
                    "content_type",
                    models.ForeignKey(
                        to="contenttypes.ContentType", on_delete=models.CASCADE
                    ),
                ),
                (
                    "index",
                    models.ForeignKey(
                        related_name="outdated_objects",
                        to="search.Index",
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
        ),
        migrations.AlterUniqueTogether(
            name="filtergroup",
            unique_together={("name", "slug")},
        ),
        migrations.AddField(
            model_name="filter",
            name="group",
            field=models.ForeignKey(
                related_name="filters",
                to="search.FilterGroup",
                help_text=b'E.g. "Topic", "Skill level" etc',
                on_delete=models.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name="filter",
            name="tags",
            field=taggit.managers.TaggableManager(
                to="taggit.Tag",
                through="taggit.TaggedItem",
                help_text=b"A comma-separated list of tags. If more than one tag given a OR query is executed",
                verbose_name="Tags",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="filter",
            unique_together={("name", "slug")},
        ),
        migrations.AddField(
            model_name="filter",
            name="default",
            field=models.BooleanField(
                default=False,
                help_text=b"Whether this filter is applied in the absence of a user-chosen filter",
            ),
        ),
        migrations.AlterField(
            model_name="filter",
            name="tags",
            field=taggit.managers.TaggableManager(
                to="taggit.Tag",
                through="taggit.TaggedItem",
                help_text=b"A comma-separated list of tags. If more than one tag given the operator specified is used",
                verbose_name="Tags",
            ),
        ),
    ]
