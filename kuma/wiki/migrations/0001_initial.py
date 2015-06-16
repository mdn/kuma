# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import kuma.core.fields
import datetime
from django.conf import settings
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        ('attachments', '0002_auto_20150430_0752'),
        ('teamwork', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255, db_index=True)),
                ('slug', models.CharField(max_length=255, db_index=True)),
                ('is_template', models.BooleanField(default=False, db_index=True, editable=False)),
                ('is_redirect', models.BooleanField(default=False, db_index=True, editable=False)),
                ('is_localizable', models.BooleanField(default=True, db_index=True)),
                ('locale', kuma.core.fields.LocaleField(default=b'en-US', max_length=7, db_index=True, choices=[(b'af', 'Afrikaans'), (b'ar', '\u0639\u0631\u0628\u064a'), (b'az', 'Az\u0259rbaycanca'), (b'bn-BD', '\u09ac\u09be\u0982\u09b2\u09be (\u09ac\u09be\u0982\u09b2\u09be\u09a6\u09c7\u09b6)'), (b'bn-IN', '\u09ac\u09be\u0982\u09b2\u09be (\u09ad\u09be\u09b0\u09a4)'), (b'ca', 'Catal\xe0'), (b'cs', '\u010ce\u0161tina'), (b'de', 'Deutsch'), (b'ee', 'E\u028be'), (b'el', '\u0395\u03bb\u03bb\u03b7\u03bd\u03b9\u03ba\u03ac'), (b'en-US', 'English (US)'), (b'es', 'Espa\xf1ol'), (b'fa', '\u0641\u0627\u0631\u0633\u06cc'), (b'ff', 'Pulaar-Fulfulde'), (b'fi', 'suomi'), (b'fr', 'Fran\xe7ais'), (b'fy-NL', 'Frysk'), (b'ga-IE', 'Gaeilge'), (b'ha', 'Hausa'), (b'he', '\u05e2\u05d1\u05e8\u05d9\u05ea'), (b'hi-IN', '\u0939\u093f\u0928\u094d\u0926\u0940 (\u092d\u093e\u0930\u0924)'), (b'hr', 'Hrvatski'), (b'hu', 'magyar'), (b'id', 'Bahasa Indonesia'), (b'ig', 'Igbo'), (b'it', 'Italiano'), (b'ja', '\u65e5\u672c\u8a9e'), (b'ka', '\u10e5\u10d0\u10e0\u10d7\u10e3\u10da\u10d8'), (b'ko', '\ud55c\uad6d\uc5b4'), (b'ln', 'Ling\xe1la'), (b'ml', '\u0d2e\u0d32\u0d2f\u0d3e\u0d33\u0d02'), (b'ms', 'Melayu'), (b'nl', 'Nederlands'), (b'pl', 'Polski'), (b'pt-BR', 'Portugu\xeas (do\xa0Brasil)'), (b'pt-PT', 'Portugu\xeas (Europeu)'), (b'ro', 'rom\xe2n\u0103'), (b'ru', '\u0420\u0443\u0441\u0441\u043a\u0438\u0439'), (b'sq', 'Shqip'), (b'sw', 'Kiswahili'), (b'ta', '\u0ba4\u0bae\u0bbf\u0bb4\u0bcd'), (b'th', '\u0e44\u0e17\u0e22'), (b'tr', 'T\xfcrk\xe7e'), (b'vi', 'Ti\u1ebfng Vi\u1ec7t'), (b'wo', 'Wolof'), (b'xh', 'isiXhosa'), (b'yo', 'Yor\xf9b\xe1'), (b'zh-CN', '\u4e2d\u6587 (\u7b80\u4f53)'), (b'zh-TW', '\u6b63\u9ad4\u4e2d\u6587 (\u7e41\u9ad4)'), (b'zu', 'isiZulu')])),
                ('json', models.TextField(null=True, editable=False, blank=True)),
                ('html', models.TextField(editable=False)),
                ('rendered_html', models.TextField(null=True, editable=False, blank=True)),
                ('rendered_errors', models.TextField(null=True, editable=False, blank=True)),
                ('defer_rendering', models.BooleanField(default=False, db_index=True)),
                ('render_scheduled_at', models.DateTimeField(null=True, db_index=True)),
                ('render_started_at', models.DateTimeField(null=True, db_index=True)),
                ('last_rendered_at', models.DateTimeField(null=True, db_index=True)),
                ('render_max_age', models.IntegerField(null=True, blank=True)),
                ('render_expires', models.DateTimeField(db_index=True, null=True, blank=True)),
                ('category', models.IntegerField(db_index=True, choices=[(0, 'Uncategorized'), (10, 'Reference')])),
                ('deleted', models.BooleanField(default=False, db_index=True)),
                ('modified', models.DateTimeField(db_index=True, auto_now=True, null=True)),
                ('body_html', models.TextField(null=True, editable=False, blank=True)),
                ('quick_links_html', models.TextField(null=True, editable=False, blank=True)),
                ('zone_subnav_local_html', models.TextField(null=True, editable=False, blank=True)),
                ('toc_html', models.TextField(null=True, editable=False, blank=True)),
                ('summary_html', models.TextField(null=True, editable=False, blank=True)),
                ('summary_text', models.TextField(null=True, editable=False, blank=True)),
            ],
            options={
                'permissions': (('view_document', 'Can view document'), ('add_template_document', 'Can add Template:* document'), ('change_template_document', 'Can change Template:* document'), ('move_tree', 'Can move a tree of documents'), ('purge_document', 'Can permanently delete document'), ('restore_document', 'Can restore deleted document')),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DocumentAttachment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.TextField()),
                ('attached_by', models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True)),
                ('document', models.ForeignKey(to='wiki.Document')),
                ('file', models.ForeignKey(to='attachments.Attachment')),
            ],
            options={
                'db_table': 'attachments_documentattachment',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DocumentDeletionLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('locale', kuma.core.fields.LocaleField(default=b'en-US', max_length=7, db_index=True, choices=[(b'af', 'Afrikaans'), (b'ar', '\u0639\u0631\u0628\u064a'), (b'az', 'Az\u0259rbaycanca'), (b'bn-BD', '\u09ac\u09be\u0982\u09b2\u09be (\u09ac\u09be\u0982\u09b2\u09be\u09a6\u09c7\u09b6)'), (b'bn-IN', '\u09ac\u09be\u0982\u09b2\u09be (\u09ad\u09be\u09b0\u09a4)'), (b'ca', 'Catal\xe0'), (b'cs', '\u010ce\u0161tina'), (b'de', 'Deutsch'), (b'ee', 'E\u028be'), (b'el', '\u0395\u03bb\u03bb\u03b7\u03bd\u03b9\u03ba\u03ac'), (b'en-US', 'English (US)'), (b'es', 'Espa\xf1ol'), (b'fa', '\u0641\u0627\u0631\u0633\u06cc'), (b'ff', 'Pulaar-Fulfulde'), (b'fi', 'suomi'), (b'fr', 'Fran\xe7ais'), (b'fy-NL', 'Frysk'), (b'ga-IE', 'Gaeilge'), (b'ha', 'Hausa'), (b'he', '\u05e2\u05d1\u05e8\u05d9\u05ea'), (b'hi-IN', '\u0939\u093f\u0928\u094d\u0926\u0940 (\u092d\u093e\u0930\u0924)'), (b'hr', 'Hrvatski'), (b'hu', 'magyar'), (b'id', 'Bahasa Indonesia'), (b'ig', 'Igbo'), (b'it', 'Italiano'), (b'ja', '\u65e5\u672c\u8a9e'), (b'ka', '\u10e5\u10d0\u10e0\u10d7\u10e3\u10da\u10d8'), (b'ko', '\ud55c\uad6d\uc5b4'), (b'ln', 'Ling\xe1la'), (b'ml', '\u0d2e\u0d32\u0d2f\u0d3e\u0d33\u0d02'), (b'ms', 'Melayu'), (b'nl', 'Nederlands'), (b'pl', 'Polski'), (b'pt-BR', 'Portugu\xeas (do\xa0Brasil)'), (b'pt-PT', 'Portugu\xeas (Europeu)'), (b'ro', 'rom\xe2n\u0103'), (b'ru', '\u0420\u0443\u0441\u0441\u043a\u0438\u0439'), (b'sq', 'Shqip'), (b'sw', 'Kiswahili'), (b'ta', '\u0ba4\u0bae\u0bbf\u0bb4\u0bcd'), (b'th', '\u0e44\u0e17\u0e22'), (b'tr', 'T\xfcrk\xe7e'), (b'vi', 'Ti\u1ebfng Vi\u1ec7t'), (b'wo', 'Wolof'), (b'xh', 'isiXhosa'), (b'yo', 'Yor\xf9b\xe1'), (b'zh-CN', '\u4e2d\u6587 (\u7b80\u4f53)'), (b'zh-TW', '\u6b63\u9ad4\u4e2d\u6587 (\u7e41\u9ad4)'), (b'zu', 'isiZulu')])),
                ('slug', models.CharField(max_length=255, db_index=True)),
                ('timestamp', models.DateTimeField(auto_now=True)),
                ('reason', models.TextField()),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DocumentTag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100, verbose_name='Name')),
                ('slug', models.SlugField(unique=True, max_length=100, verbose_name='Slug')),
            ],
            options={
                'verbose_name': 'Document Tag',
                'verbose_name_plural': 'Document Tags',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DocumentZone',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('styles', models.TextField(null=True, blank=True)),
                ('url_root', models.CharField(help_text=b'alternative URL path root for documents under this zone', max_length=255, null=True, db_index=True, blank=True)),
                ('document', models.OneToOneField(related_name='zone', to='wiki.Document')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='EditorToolbar',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('default', models.BooleanField(default=False)),
                ('name', models.CharField(max_length=100)),
                ('code', models.TextField(max_length=2000)),
                ('creator', models.ForeignKey(related_name='created_toolbars', to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='HelpfulVote',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('helpful', models.BooleanField(default=False)),
                ('created', models.DateTimeField(default=datetime.datetime.now, db_index=True)),
                ('anonymous_id', models.CharField(max_length=40, db_index=True)),
                ('user_agent', models.CharField(max_length=1000)),
                ('creator', models.ForeignKey(related_name='poll_votes', to=settings.AUTH_USER_MODEL, null=True)),
                ('document', models.ForeignKey(related_name='poll_votes', to='wiki.Document')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='LocalizationTag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100, verbose_name='Name')),
                ('slug', models.SlugField(unique=True, max_length=100, verbose_name='Slug')),
            ],
            options={
                'verbose_name': 'Localization Tag',
                'verbose_name_plural': 'Localization Tags',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='LocalizationTaggedRevision',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ReviewTag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100, verbose_name='Name')),
                ('slug', models.SlugField(unique=True, max_length=100, verbose_name='Slug')),
            ],
            options={
                'verbose_name': 'Review Tag',
                'verbose_name_plural': 'Review Tags',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ReviewTaggedRevision',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Revision',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255, null=True, db_index=True)),
                ('slug', models.CharField(max_length=255, null=True, db_index=True)),
                ('summary', models.TextField()),
                ('content', models.TextField()),
                ('keywords', models.CharField(max_length=255, blank=True)),
                ('tags', models.CharField(max_length=255, blank=True)),
                ('toc_depth', models.IntegerField(default=1, choices=[(0, 'No table of contents'), (1, 'All levels'), (2, 'H2 and higher'), (3, 'H3 and higher'), (4, 'H4 and higher')])),
                ('render_max_age', models.IntegerField(null=True, blank=True)),
                ('created', models.DateTimeField(default=datetime.datetime.now, db_index=True)),
                ('comment', models.CharField(max_length=255)),
                ('is_approved', models.BooleanField(default=True, db_index=True)),
                ('is_mindtouch_migration', models.BooleanField(default=False, help_text=b'Did this revision come from MindTouch?', db_index=True)),
                ('based_on', models.ForeignKey(blank=True, to='wiki.Revision', null=True)),
                ('creator', models.ForeignKey(related_name='created_revisions', to=settings.AUTH_USER_MODEL)),
                ('document', models.ForeignKey(related_name='revisions', to='wiki.Document')),
                ('localization_tags', taggit.managers.TaggableManager(to='wiki.LocalizationTag', through='wiki.LocalizationTaggedRevision', help_text='A comma-separated list of tags.', verbose_name='Tags')),
                ('review_tags', taggit.managers.TaggableManager(to='wiki.ReviewTag', through='wiki.ReviewTaggedRevision', help_text='A comma-separated list of tags.', verbose_name='Tags')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='RevisionIP',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ip', models.CharField(db_index=True, max_length=40, null=True, editable=False, blank=True)),
                ('revision', models.ForeignKey(to='wiki.Revision')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TaggedDocument',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('content_object', models.ForeignKey(to='wiki.Document')),
                ('tag', models.ForeignKey(to='wiki.DocumentTag')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='reviewtaggedrevision',
            name='content_object',
            field=models.ForeignKey(to='wiki.Revision'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='reviewtaggedrevision',
            name='tag',
            field=models.ForeignKey(to='wiki.ReviewTag'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='localizationtaggedrevision',
            name='content_object',
            field=models.ForeignKey(to='wiki.Revision'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='localizationtaggedrevision',
            name='tag',
            field=models.ForeignKey(to='wiki.LocalizationTag'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='document',
            name='current_revision',
            field=models.ForeignKey(related_name='current_for+', to='wiki.Revision', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='document',
            name='files',
            field=models.ManyToManyField(to='attachments.Attachment', through='wiki.DocumentAttachment'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='document',
            name='parent',
            field=models.ForeignKey(related_name='translations', blank=True, to='wiki.Document', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='document',
            name='parent_topic',
            field=models.ForeignKey(related_name='children', blank=True, to='wiki.Document', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='document',
            name='tags',
            field=taggit.managers.TaggableManager(to='wiki.DocumentTag', through='wiki.TaggedDocument', help_text='A comma-separated list of tags.', verbose_name='Tags'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='document',
            name='team',
            field=models.ForeignKey(blank=True, to='teamwork.Team', null=True),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='document',
            unique_together=set([('parent', 'locale'), ('slug', 'locale')]),
        ),
    ]
