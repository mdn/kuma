# Generated by Django 1.11.23 on 2019-09-14 22:08


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0010_auto_20190912_1634"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="locale",
            field=models.CharField(
                blank=True,
                choices=[
                    (b"en-US", "English (US)"),
                    (b"ar", "\u0639\u0631\u0628\u064a"),
                    (b"bg", "\u0411\u044a\u043b\u0433\u0430\u0440\u0441\u043a\u0438"),
                    (b"bm", "Bamanankan"),
                    (b"bn", "\u09ac\u09be\u0982\u09b2\u09be"),
                    (b"ca", "Catal\xe0"),
                    (b"de", "Deutsch"),
                    (b"el", "\u0395\u03bb\u03bb\u03b7\u03bd\u03b9\u03ba\u03ac"),
                    (b"es", "Espa\xf1ol"),
                    (b"fa", "\u0641\u0627\u0631\u0633\u06cc"),
                    (b"fi", "suomi"),
                    (b"fr", "Fran\xe7ais"),
                    (b"he", "\u05e2\u05d1\u05e8\u05d9\u05ea"),
                    (
                        b"hi-IN",
                        "\u0939\u093f\u0928\u094d\u0926\u0940 (\u092d\u093e\u0930\u0924)",
                    ),
                    (b"hu", "magyar"),
                    (b"id", "Bahasa Indonesia"),
                    (b"it", "Italiano"),
                    (b"ja", "\u65e5\u672c\u8a9e"),
                    (b"kab", "Taqbaylit"),
                    (b"ko", "\ud55c\uad6d\uc5b4"),
                    (b"ms", "Melayu"),
                    (
                        b"my",
                        "\u1019\u103c\u1014\u103a\u1019\u102c\u1018\u102c\u101e\u102c",
                    ),
                    (b"nl", "Nederlands"),
                    (b"pl", "Polski"),
                    (b"pt-BR", "Portugu\xeas (do\xa0Brasil)"),
                    (b"pt-PT", "Portugu\xeas (Europeu)"),
                    (b"ru", "\u0420\u0443\u0441\u0441\u043a\u0438\u0439"),
                    (b"sv-SE", "Svenska"),
                    (b"th", "\u0e44\u0e17\u0e22"),
                    (b"tr", "T\xfcrk\xe7e"),
                    (
                        b"uk",
                        "\u0423\u043a\u0440\u0430\u0457\u043d\u0441\u044c\u043a\u0430",
                    ),
                    (b"vi", "Ti\u1ebfng Vi\u1ec7t"),
                    (b"zh-CN", "\u4e2d\u6587 (\u7b80\u4f53)"),
                    (b"zh-TW", "\u6b63\u9ad4\u4e2d\u6587 (\u7e41\u9ad4)"),
                ],
                db_index=True,
                default=b"en-US",
                max_length=7,
                verbose_name="Language",
            ),
        ),
    ]
