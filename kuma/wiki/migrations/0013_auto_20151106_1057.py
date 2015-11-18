# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
import django.db.models.deletion
from django.conf import settings
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('wiki', '0012_auto_20151105_1131'),
    ]

    operations = [
        migrations.CreateModel(
            name='RevisionAkismetSubmission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sent', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='sent at', db_index=True, editable=False, blank=True)),
                ('type', models.CharField(db_index=True, max_length=4, verbose_name='submission type', choices=[(b'spam', 'Spam'), (b'ham', 'Ham')])),
                ('revision', models.ForeignKey(related_name='akismet_submissions', on_delete=django.db.models.deletion.SET_NULL, verbose_name=b'Revision', blank=True, to='wiki.Revision', null=True)),
                ('sender', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-sent',),
                'abstract': False,
                'get_latest_by': 'sent',
            },
            bases=(models.Model,),
        ),
    ]
