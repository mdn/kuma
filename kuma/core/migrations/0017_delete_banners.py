from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0016_delete_django_constance"),
    ]

    operations = [
        migrations.RunSQL("DROP TABLE IF EXISTS banners_banner"),
    ]
