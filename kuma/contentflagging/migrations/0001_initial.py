# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ContentFlag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('flag_status', models.CharField(default=b'flagged', max_length=16, verbose_name='current status of flag review', choices=[(b'flagged', 'Flagged'), (b'rejected', 'Flag rejected by moderator'), (b'notified', 'Creator notified'), (b'hidden', 'Content hidden by moderator'), (b'deleted', 'Content deleted by moderator')])),
                ('flag_type', models.CharField(db_index=True, max_length=64, verbose_name='reason for flagging the content', choices=[(b'notworking', 'This demo is not working for me'), (b'inappropriate', 'This demo contains inappropriate content'), (b'plagarised', 'This demo was not created by the author'), (b'bad', 'This article is spam/inappropriate'), (b'unneeded', 'This article is obsolete/unneeded'), (b'duplicate', 'This is a duplicate of another article')])),
                ('explanation', models.TextField(max_length=255, verbose_name='please explain what content you feel is inappropriate', blank=True)),
                ('object_pk', models.CharField(verbose_name='object ID', max_length=32, editable=False)),
                ('ip', models.CharField(max_length=40, null=True, editable=False, blank=True)),
                ('user_agent', models.CharField(max_length=128, null=True, editable=False, blank=True)),
                ('unique_hash', models.CharField(max_length=32, unique=True, null=True, editable=False, db_index=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='date submitted')),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='date last modified')),
                ('content_type', models.ForeignKey(related_name='content_type_set_for_contentflag', editable=False, to='contenttypes.ContentType', verbose_name=b'content type')),
            ],
            options={
                'ordering': ('-created',),
                'get_latest_by': 'created',
            },
            bases=(models.Model,),
        ),
    ]
