# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ActionCounterUnique',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_pk', models.CharField(max_length=32, verbose_name='object ID')),
                ('name', models.CharField(max_length=64, verbose_name='name of the action', db_index=True)),
                ('total', models.IntegerField()),
                ('ip', models.CharField(db_index=True, max_length=40, null=True, editable=False, blank=True)),
                ('user_agent', models.CharField(db_index=True, max_length=128, null=True, editable=False, blank=True)),
                ('unique_hash', models.CharField(max_length=32, unique=True, null=True, editable=False, db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='date last modified')),
                ('content_type', models.ForeignKey(related_name='content_type_set_for_actioncounterunique', verbose_name=b'content type', to='contenttypes.ContentType')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
