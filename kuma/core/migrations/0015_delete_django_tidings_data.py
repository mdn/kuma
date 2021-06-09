from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0014_delete_django_soapbox_data"),
    ]

    operations = [
        migrations.RunSQL("DROP TABLE IF EXISTS tidings_watchfilter"),
        migrations.RunSQL("DROP TABLE IF EXISTS tidings_watch"),
    ]
