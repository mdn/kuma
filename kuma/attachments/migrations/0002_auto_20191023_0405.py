# Generated by Django 1.11.23 on 2019-10-23 04:05


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("attachments", "0001_squashed_0008_attachment_on_delete"),
    ]

    operations = [
        migrations.AlterField(
            model_name="attachment",
            name="mindtouch_attachment_id",
            field=models.IntegerField(
                blank=True,
                db_index=True,
                help_text="ID for migrated MindTouch resource",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="attachmentrevision",
            name="is_mindtouch_migration",
            field=models.BooleanField(
                db_index=True,
                default=False,
                help_text="Did this revision come from MindTouch?",
            ),
        ),
        migrations.AlterField(
            model_name="attachmentrevision",
            name="mime_type",
            field=models.CharField(
                blank=True,
                db_index=True,
                default="application/octet-stream",
                help_text="The MIME type is used when serving the attachment. Automatically populated by inspecting the file on upload. Please only override if needed.",
                max_length=255,
            ),
        ),
        migrations.AlterField(
            model_name="attachmentrevision",
            name="mindtouch_old_id",
            field=models.IntegerField(
                blank=True,
                db_index=True,
                help_text="ID for migrated MindTouch resource revision",
                null=True,
                unique=True,
            ),
        ),
    ]
