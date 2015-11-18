# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wiki', '0013_auto_20151106_1057'),
    ]

    operations = [
        migrations.AddField(
            model_name='revisionip',
            name='referrer',
            field=models.TextField(verbose_name=b'HTTP Referrer', editable=False, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='revisionip',
            name='user_agent',
            field=models.TextField(verbose_name=b'User-Agent', editable=False, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='revisionip',
            name='ip',
            field=models.CharField(editable=False, max_length=40, blank=True, null=True, verbose_name=b'IP address', db_index=True),
            preserve_default=True,
        ),
    ]
