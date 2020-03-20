import datetime

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import kuma.attachments.utils


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Attachment",
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
                ("title", models.CharField(max_length=255, db_index=True)),
                (
                    "mindtouch_attachment_id",
                    models.IntegerField(
                        help_text=b"ID for migrated MindTouch resource",
                        null=True,
                        db_index=True,
                    ),
                ),
                (
                    "modified",
                    models.DateTimeField(db_index=True, auto_now=True, null=True),
                ),
            ],
            options={
                "permissions": (
                    ("disallow_add_attachment", "Cannot upload attachment"),
                ),
            },
        ),
        migrations.CreateModel(
            name="AttachmentRevision",
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
                    "file",
                    models.FileField(
                        max_length=500,
                        upload_to=kuma.attachments.utils.attachment_upload_to,
                    ),
                ),
                ("title", models.CharField(max_length=255, null=True, db_index=True)),
                ("mime_type", models.CharField(max_length=255, db_index=True)),
                ("description", models.TextField(blank=True)),
                ("created", models.DateTimeField(default=datetime.datetime.now)),
                ("comment", models.CharField(max_length=255, blank=True)),
                ("is_approved", models.BooleanField(default=True, db_index=True)),
                (
                    "mindtouch_old_id",
                    models.IntegerField(
                        help_text=b"ID for migrated MindTouch resource revision",
                        unique=True,
                        null=True,
                        db_index=True,
                    ),
                ),
                (
                    "is_mindtouch_migration",
                    models.BooleanField(
                        default=False,
                        help_text=b"Did this revision come from MindTouch?",
                        db_index=True,
                    ),
                ),
                (
                    "attachment",
                    models.ForeignKey(
                        related_name="revisions",
                        to="attachments.Attachment",
                        on_delete=models.CASCADE,
                    ),
                ),
                (
                    "creator",
                    models.ForeignKey(
                        related_name="created_attachment_revisions",
                        to=settings.AUTH_USER_MODEL,
                        on_delete=models.PROTECT,
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="attachment",
            name="current_revision",
            field=models.ForeignKey(
                related_name="current_for+",
                on_delete=django.db.models.deletion.SET_NULL,
                blank=True,
                to="attachments.AttachmentRevision",
                null=True,
            ),
        ),
        migrations.AlterModelOptions(
            name="attachmentrevision",
            options={
                "verbose_name": "attachment revision",
                "verbose_name_plural": "attachment revisions",
            },
        ),
        migrations.AlterField(
            model_name="attachment",
            name="mindtouch_attachment_id",
            field=models.IntegerField(
                help_text=b"ID for migrated MindTouch resource",
                null=True,
                db_index=True,
                blank=True,
            ),
        ),
        migrations.AlterField(
            model_name="attachmentrevision",
            name="mindtouch_old_id",
            field=models.IntegerField(
                help_text=b"ID for migrated MindTouch resource revision",
                unique=True,
                null=True,
                db_index=True,
                blank=True,
            ),
        ),
        migrations.AlterField(
            model_name="attachmentrevision",
            name="mime_type",
            field=models.CharField(
                default=b"application/octet-stream", max_length=255, db_index=True
            ),
        ),
        migrations.AlterField(
            model_name="attachmentrevision",
            name="mime_type",
            field=models.CharField(
                default=b"application/octet-stream",
                help_text="The MIME type is used when serving the attachment. Automatically populated by inspecting the file on upload. Please only override if needed.",
                max_length=255,
                db_index=True,
                blank=True,
            ),
        ),
        migrations.CreateModel(
            name="TrashedAttachment",
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
                    "file",
                    models.FileField(
                        help_text="The attachment file that was trashed",
                        max_length=500,
                        upload_to=kuma.attachments.utils.attachment_upload_to,
                    ),
                ),
                (
                    "trashed_at",
                    models.DateTimeField(
                        default=datetime.datetime.now,
                        help_text="The date and time the attachment was trashed",
                    ),
                ),
                (
                    "trashed_by",
                    models.CharField(
                        help_text="The username of the user who trashed the attachment",
                        max_length=30,
                        blank=True,
                    ),
                ),
                (
                    "was_current",
                    models.BooleanField(
                        default=False,
                        help_text="Whether or not this attachment was the current attachment revision at the time of trashing.",
                    ),
                ),
            ],
            options={
                "verbose_name": "Trashed attachment",
                "verbose_name_plural": "Trashed attachments",
            },
        ),
    ]
