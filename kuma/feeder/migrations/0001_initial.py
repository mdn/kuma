# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Bundle',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('shortname', models.SlugField(help_text=b'Short name to find this bundle by.', unique=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Entry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('guid', models.CharField(max_length=255)),
                ('raw', models.TextField()),
                ('visible', models.BooleanField(default=True)),
                ('last_published', models.DateTimeField()),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name=b'Created On')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name=b'Last Modified')),
            ],
            options={
                'ordering': ['-last_published'],
                'verbose_name_plural': 'Entries',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Feed',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('shortname', models.SlugField(help_text=b'Short name to find this feed by.', unique=True)),
                ('title', models.CharField(max_length=140)),
                ('url', models.CharField(max_length=2048)),
                ('etag', models.CharField(max_length=140)),
                ('last_modified', models.DateTimeField()),
                ('enabled', models.BooleanField(default=True)),
                ('disabled_reason', models.CharField(max_length=2048, blank=True)),
                ('keep', models.PositiveIntegerField(default=0, help_text=b'Discard all but this amount of entries. 0 == do not discard.')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name=b'Created On')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name=b'Last Modified')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='entry',
            name='feed',
            field=models.ForeignKey(related_name='entries', to='feeder.Feed'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='entry',
            unique_together=set([('feed', 'guid')]),
        ),
        migrations.AddField(
            model_name='bundle',
            name='feeds',
            field=models.ManyToManyField(related_name='bundles', to='feeder.Feed', blank=True),
            preserve_default=True,
        ),
    ]
