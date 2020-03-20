from django.core.exceptions import ObjectDoesNotExist
from django.db import migrations


def remove_view_document_permission(apps, schema_editor):
    """
    Delete our legacy view_document permission, which conflicts with the default
    permissions added by Django 2.1.
    """
    Permission = apps.get_model("auth.Permission")
    ContentType = apps.get_model("contenttypes.ContentType")

    try:
        content_type = ContentType.objects.get(app_label="wiki", model="document")
        Permission.objects.get(
            content_type=content_type, codename=("view_document")
        ).delete()
    except ObjectDoesNotExist:
        # The ContentType and Permission may not exist on a new, empty database,
        # like in our CI environment. And that's OK.
        pass


class Migration(migrations.Migration):

    dependencies = [
        ("wiki", "0006_auto_20191023_0741"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="document",
            options={
                "permissions": (
                    ("move_tree", "Can move a tree of documents"),
                    ("purge_document", "Can permanently delete document"),
                    ("restore_document", "Can restore deleted document"),
                )
            },
        ),
        migrations.RunPython(
            remove_view_document_permission, migrations.RunPython.noop
        ),
    ]
