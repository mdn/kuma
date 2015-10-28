# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
from django.conf import settings
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('wiki', '0009_remove_share_url'),
    ]

    operations = [
        migrations.CreateModel(
            name='DocumentSpamAttempt',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', db_index=True, editable=False, blank=True)),
                ('title', models.CharField(max_length=255, verbose_name=b'Title')),
                ('slug', models.CharField(max_length=255, verbose_name=b'Slug')),
                ('document', models.ForeignKey(related_name='spam_attempts', verbose_name=b'Edited/translated document (optional)', blank=True, to='wiki.Document', null=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-created',),
                'abstract': False,
                'get_latest_by': 'created',
            },
            bases=(models.Model,),
        ),
    ]
