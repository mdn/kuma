# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contentflagging', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='contentflag',
            name='user',
            field=models.ForeignKey(blank=True, editable=False, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
    ]
