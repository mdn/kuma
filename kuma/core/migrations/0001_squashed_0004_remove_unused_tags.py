# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    replaces = [(b'core', '0001_initial'), (b'core', '0002_remove_demos'), (b'core', '0003_remove_unused_taggeditems'), (b'core', '0004_remove_unused_tags')]

    dependencies = [
        ('taggit', '0002_auto_20150616_2121'),
    ]

    operations = [
        migrations.CreateModel(
            name='IPBan',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ip', models.GenericIPAddressField()),
                ('created', models.DateTimeField(default=django.utils.timezone.now, db_index=True)),
                ('deleted', models.DateTimeField(null=True, blank=True)),
            ],
        ),
    ]
