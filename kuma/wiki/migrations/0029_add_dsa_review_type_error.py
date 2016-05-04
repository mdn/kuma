# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wiki', '0028_require_document_uuid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='documentspamattempt',
            name='review',
            field=models.IntegerField(default=0, verbose_name="Review of Akismet's classification as spam", choices=[(0, 'Needs Review'), (1, 'Ham / False Positive'), (2, 'Confirmed as Spam'), (3, 'Review Unavailable'), (4, 'Akismet Error')]),
        ),
    ]
