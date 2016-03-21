# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('wiki', '0023_add_document_uuid'),
    ]

    operations = [
        migrations.AddField(
            model_name='documentspamattempt',
            name='data',
            field=models.TextField(verbose_name='Data submitted to Akismet', null=True, editable=False, blank=True),
        ),
        migrations.AddField(
            model_name='documentspamattempt',
            name='review',
            field=models.IntegerField(default=0, verbose_name="Review of Akismet's classification as spam", choices=[(0, 'Needs Review'), (1, 'Ham / False Positive'), (2, 'Confirmed as Spam'), (3, 'Review Unavailable')]),
        ),
        migrations.AddField(
            model_name='documentspamattempt',
            name='reviewed',
            field=models.DateTimeField(null=True, verbose_name='reviewed', blank=True),
        ),
        migrations.AddField(
            model_name='documentspamattempt',
            name='reviewer',
            field=models.ForeignKey(related_name='documentspam_reviewed', verbose_name='Staff reviewer', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
    ]
