import functools
import json

from django.core.management.base import BaseCommand, CommandError

from kuma.notifications.models import CompatibilityData, Notification

from kuma.notifications.extract import generators, walk


def get_feature(bcd, feature):
    try:
        return functools.reduce(dict.get, feature.split("."), bcd)["__compat"]
    except (TypeError, KeyError):
        return None


class Command(BaseCommand):
    help = "Extracts notifications from a bcd.json file"

    def handle(self, *args, **options):
        latest = CompatibilityData.objects.all().order_by("created").last()
        old_bcd = json.loads(latest.bcd)
        bcd = json.loads(open("bcd.json").read())
        for key, feature in walk(bcd):
            old_feature = get_feature(old_bcd, key)
            for gen in generators:
                for notification in gen(key, old_feature, feature).generate():
                    print(notification)
