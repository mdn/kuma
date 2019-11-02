

from django.conf import settings
from django.core.management.base import BaseCommand

from kuma.wiki.tasks import build_index_sitemap, build_locale_sitemap


class Command(BaseCommand):
    help = ("Create sitemap files for every MDN language, "
            "as well as a sitemap index file.")

    def handle(self, *args, **options):
        build_index_sitemap(build_locale_sitemap(lang[0])
                            for lang in settings.LANGUAGES)
