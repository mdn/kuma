from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0015_delete_django_tidings_data"),
    ]

    operations = [
        migrations.RunSQL("DROP TABLE IF EXISTS constance_config"),
    ]
