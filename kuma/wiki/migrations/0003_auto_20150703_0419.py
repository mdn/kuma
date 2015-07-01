# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import kuma.core.fields


class Migration(migrations.Migration):

    dependencies = [
        ('wiki', '0002_auto_20150430_0805'),
    ]

    operations = [
        migrations.AlterField(
            model_name='document',
            name='locale',
            field=kuma.core.fields.LocaleField(default=b'en-US', max_length=7, db_index=True, choices=[(b'af', 'Afrikaans'), (b'ar', '\u0639\u0631\u0628\u064a'), (b'az', 'Az\u0259rbaycanca'), (b'bm', 'Bamanankan'), (b'bn-BD', '\u09ac\u09be\u0982\u09b2\u09be (\u09ac\u09be\u0982\u09b2\u09be\u09a6\u09c7\u09b6)'), (b'bn-IN', '\u09ac\u09be\u0982\u09b2\u09be (\u09ad\u09be\u09b0\u09a4)'), (b'ca', 'Catal\xe0'), (b'cs', '\u010ce\u0161tina'), (b'de', 'Deutsch'), (b'ee', 'E\u028be'), (b'el', '\u0395\u03bb\u03bb\u03b7\u03bd\u03b9\u03ba\u03ac'), (b'en-US', 'English (US)'), (b'es', 'Espa\xf1ol'), (b'fa', '\u0641\u0627\u0631\u0633\u06cc'), (b'ff', 'Pulaar-Fulfulde'), (b'fi', 'suomi'), (b'fr', 'Fran\xe7ais'), (b'fy-NL', 'Frysk'), (b'ga-IE', 'Gaeilge'), (b'ha', 'Hausa'), (b'he', '\u05e2\u05d1\u05e8\u05d9\u05ea'), (b'hi-IN', '\u0939\u093f\u0928\u094d\u0926\u0940 (\u092d\u093e\u0930\u0924)'), (b'hr', 'Hrvatski'), (b'hu', 'magyar'), (b'id', 'Bahasa Indonesia'), (b'ig', 'Igbo'), (b'it', 'Italiano'), (b'ja', '\u65e5\u672c\u8a9e'), (b'ka', '\u10e5\u10d0\u10e0\u10d7\u10e3\u10da\u10d8'), (b'ko', '\ud55c\uad6d\uc5b4'), (b'ln', 'Ling\xe1la'), (b'ml', '\u0d2e\u0d32\u0d2f\u0d3e\u0d33\u0d02'), (b'ms', 'Melayu'), (b'my', '\u1019\u103c\u1014\u103a\u1019\u102c\u1018\u102c\u101e\u102c'), (b'nl', 'Nederlands'), (b'pl', 'Polski'), (b'pt-BR', 'Portugu\xeas (do\xa0Brasil)'), (b'pt-PT', 'Portugu\xeas (Europeu)'), (b'ro', 'rom\xe2n\u0103'), (b'ru', '\u0420\u0443\u0441\u0441\u043a\u0438\u0439'), (b'son', 'So\u014bay'), (b'sq', 'Shqip'), (b'sw', 'Kiswahili'), (b'ta', '\u0ba4\u0bae\u0bbf\u0bb4\u0bcd'), (b'th', '\u0e44\u0e17\u0e22'), (b'tl', 'Tagalog'), (b'tr', 'T\xfcrk\xe7e'), (b'vi', 'Ti\u1ebfng Vi\u1ec7t'), (b'wo', 'Wolof'), (b'xh', 'isiXhosa'), (b'yo', 'Yor\xf9b\xe1'), (b'zh-CN', '\u4e2d\u6587 (\u7b80\u4f53)'), (b'zh-TW', '\u6b63\u9ad4\u4e2d\u6587 (\u7e41\u9ad4)'), (b'zu', 'isiZulu')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='documentdeletionlog',
            name='locale',
            field=kuma.core.fields.LocaleField(default=b'en-US', max_length=7, db_index=True, choices=[(b'af', 'Afrikaans'), (b'ar', '\u0639\u0631\u0628\u064a'), (b'az', 'Az\u0259rbaycanca'), (b'bm', 'Bamanankan'), (b'bn-BD', '\u09ac\u09be\u0982\u09b2\u09be (\u09ac\u09be\u0982\u09b2\u09be\u09a6\u09c7\u09b6)'), (b'bn-IN', '\u09ac\u09be\u0982\u09b2\u09be (\u09ad\u09be\u09b0\u09a4)'), (b'ca', 'Catal\xe0'), (b'cs', '\u010ce\u0161tina'), (b'de', 'Deutsch'), (b'ee', 'E\u028be'), (b'el', '\u0395\u03bb\u03bb\u03b7\u03bd\u03b9\u03ba\u03ac'), (b'en-US', 'English (US)'), (b'es', 'Espa\xf1ol'), (b'fa', '\u0641\u0627\u0631\u0633\u06cc'), (b'ff', 'Pulaar-Fulfulde'), (b'fi', 'suomi'), (b'fr', 'Fran\xe7ais'), (b'fy-NL', 'Frysk'), (b'ga-IE', 'Gaeilge'), (b'ha', 'Hausa'), (b'he', '\u05e2\u05d1\u05e8\u05d9\u05ea'), (b'hi-IN', '\u0939\u093f\u0928\u094d\u0926\u0940 (\u092d\u093e\u0930\u0924)'), (b'hr', 'Hrvatski'), (b'hu', 'magyar'), (b'id', 'Bahasa Indonesia'), (b'ig', 'Igbo'), (b'it', 'Italiano'), (b'ja', '\u65e5\u672c\u8a9e'), (b'ka', '\u10e5\u10d0\u10e0\u10d7\u10e3\u10da\u10d8'), (b'ko', '\ud55c\uad6d\uc5b4'), (b'ln', 'Ling\xe1la'), (b'ml', '\u0d2e\u0d32\u0d2f\u0d3e\u0d33\u0d02'), (b'ms', 'Melayu'), (b'my', '\u1019\u103c\u1014\u103a\u1019\u102c\u1018\u102c\u101e\u102c'), (b'nl', 'Nederlands'), (b'pl', 'Polski'), (b'pt-BR', 'Portugu\xeas (do\xa0Brasil)'), (b'pt-PT', 'Portugu\xeas (Europeu)'), (b'ro', 'rom\xe2n\u0103'), (b'ru', '\u0420\u0443\u0441\u0441\u043a\u0438\u0439'), (b'son', 'So\u014bay'), (b'sq', 'Shqip'), (b'sw', 'Kiswahili'), (b'ta', '\u0ba4\u0bae\u0bbf\u0bb4\u0bcd'), (b'th', '\u0e44\u0e17\u0e22'), (b'tl', 'Tagalog'), (b'tr', 'T\xfcrk\xe7e'), (b'vi', 'Ti\u1ebfng Vi\u1ec7t'), (b'wo', 'Wolof'), (b'xh', 'isiXhosa'), (b'yo', 'Yor\xf9b\xe1'), (b'zh-CN', '\u4e2d\u6587 (\u7b80\u4f53)'), (b'zh-TW', '\u6b63\u9ad4\u4e2d\u6587 (\u7e41\u9ad4)'), (b'zu', 'isiZulu')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='localizationtaggedrevision',
            name='tag',
            field=models.ForeignKey(related_name='wiki_localizationtaggedrevision_items', to='wiki.LocalizationTag'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='reviewtaggedrevision',
            name='tag',
            field=models.ForeignKey(related_name='wiki_reviewtaggedrevision_items', to='wiki.ReviewTag'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='taggeddocument',
            name='tag',
            field=models.ForeignKey(related_name='wiki_taggeddocument_items', to='wiki.DocumentTag'),
            preserve_default=True,
        ),
    ]
