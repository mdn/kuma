# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.files.storage
import kuma.demos.models
import kuma.demos.embed


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Submission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(unique=True, max_length=255, verbose_name="what is your demo's name?")),
                ('slug', models.SlugField(unique=True, verbose_name='slug')),
                ('summary', models.CharField(max_length=255, verbose_name='describe your demo in one line')),
                ('description', models.TextField(verbose_name='describe your demo in more detail (optional)', blank=True)),
                ('featured', models.BooleanField(default=False)),
                ('hidden', models.BooleanField(default=False, verbose_name='Hide this demo from others?')),
                ('censored', models.BooleanField(default=False)),
                ('censored_url', models.URLField(null=True, verbose_name='Redirect URL for censorship.', blank=True)),
                ('navbar_optout', models.BooleanField(default=False, verbose_name='control how your demo is launched', choices=[(True, 'Disable navigation bar, launch demo in a new window'), (False, 'Use navigation bar, display demo in <iframe>')])),
                ('comments_total', models.PositiveIntegerField(default=0)),
                ('screenshot_1', kuma.demos.models.ReplacingImageWithThumbField(storage=django.core.files.storage.FileSystemStorage(base_url=b'/media/uploads/demos/', location=b'/Users/jezdez/Code/git/kuma/media/uploads/demos'), upload_to=kuma.demos.models.upload_screenshot_1, max_length=255, verbose_name='Screenshot #1')),
                ('screenshot_2', kuma.demos.models.ReplacingImageWithThumbField(storage=django.core.files.storage.FileSystemStorage(base_url=b'/media/uploads/demos/', location=b'/Users/jezdez/Code/git/kuma/media/uploads/demos'), upload_to=kuma.demos.models.upload_screenshot_2, max_length=255, verbose_name='Screenshot #2', blank=True)),
                ('screenshot_3', kuma.demos.models.ReplacingImageWithThumbField(storage=django.core.files.storage.FileSystemStorage(base_url=b'/media/uploads/demos/', location=b'/Users/jezdez/Code/git/kuma/media/uploads/demos'), upload_to=kuma.demos.models.upload_screenshot_3, max_length=255, verbose_name='Screenshot #3', blank=True)),
                ('screenshot_4', kuma.demos.models.ReplacingImageWithThumbField(storage=django.core.files.storage.FileSystemStorage(base_url=b'/media/uploads/demos/', location=b'/Users/jezdez/Code/git/kuma/media/uploads/demos'), upload_to=kuma.demos.models.upload_screenshot_4, max_length=255, verbose_name='Screenshot #4', blank=True)),
                ('screenshot_5', kuma.demos.models.ReplacingImageWithThumbField(storage=django.core.files.storage.FileSystemStorage(base_url=b'/media/uploads/demos/', location=b'/Users/jezdez/Code/git/kuma/media/uploads/demos'), upload_to=kuma.demos.models.upload_screenshot_5, max_length=255, verbose_name='Screenshot #5', blank=True)),
                ('video_url', kuma.demos.embed.VideoEmbedURLField(null=True, verbose_name='have a video of your demo in action? (optional)', blank=True)),
                ('demo_package', kuma.demos.models.ReplacingZipFileField(storage=django.core.files.storage.FileSystemStorage(base_url=b'/media/uploads/demos/', location=b'/Users/jezdez/Code/git/kuma/media/uploads/demos'), upload_to=kuma.demos.models.demo_package_upload_to, max_length=255, verbose_name='select a ZIP file containing your demo')),
                ('source_code_url', models.URLField(null=True, verbose_name='Is your source code also available somewhere else on the web (e.g., github)? Please share the link.', blank=True)),
                ('license_name', models.CharField(max_length=64, verbose_name='Select the license that applies to your source code.', choices=[(b'gpl', 'GPL'), (b'bsd', 'BSD'), (b'mpl', 'MPL/GPL/LGPL'), (b'publicdomain', 'Public Domain (where applicable by law)'), (b'apache', 'Apache')])),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='date created')),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='date last modified')),
                ('likes_total', models.IntegerField(default=0, db_index=True, editable=False, blank=True)),
                ('likes_recent', models.IntegerField(default=0, db_index=True, editable=False, blank=True)),
                ('launches_total', models.IntegerField(default=0, db_index=True, editable=False, blank=True)),
                ('launches_recent', models.IntegerField(default=0, db_index=True, editable=False, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
