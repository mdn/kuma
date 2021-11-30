import argparse
import functools
import json
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError

from kuma.notifications.models import (
    CompatibilityData,
    Notification,
    Watch,
    NotificationData,
)

from kuma.notifications.extract import generators, walk


def get_feature(bcd, feature):
    try:
        return functools.reduce(dict.get, feature.split("."), bcd)
    except (TypeError, KeyError):
        return None


class Command(BaseCommand):
    help = "Extracts notifications from a bcd.json file"

    def add_arguments(self, parser):
        parser.add_argument('--test-all', default=False, action='store_true')
        parser.add_argument('--load-initial', default=False, action='store_true')
        parser.add_argument("file", type=open)

    def handle(self, *args, **options):
        new_bcd = json.loads(options["file"].read())
        load_initial = options['load_initial']
        latest = CompatibilityData.objects.all().order_by("created").last()

        if not latest:
            if load_initial:
                print('Loading file as initial data...')
                CompatibilityData.objects.create(bcd=new_bcd)
            else:
                print("You need to load the initial BCD data before running this command")
            return

        old_bcd = latest.bcd

        if options['test_all']:
            for obj in walk(new_bcd):
                path = obj[0]
                for gen in generators:
                    print('\nprocessing generator')
                    before = datetime.now()
                    done = datetime.now()
                    for notification in gen(path, old_bcd, new_bcd).generate():
                        generated = datetime.now()
                        print(notification)
                        done = datetime.now()
                        print('printed notification', done - generated)
                        print('processed notification', done - before)
                    print('finished generator', done-before)
            return

        for watched in Watch.objects.distinct("path"):
            for gen in generators:
                for notification in gen(watched.path, old_bcd, new_bcd).generate():
                    print(notification)
                    obj = NotificationData.objects.create(
                        title=watched.title,
                        text=notification,
                    )
                    for user in watched.users.all():
                        Notification.objects.create(
                            notification=obj, user=user, read=False
                        )

            # for key, feature in walk(get_feature(bcd, watched.path), path=watched.path):
            #     old_feature = get_feature(old_bcd, key)

        # Replace the old compatibility data
        CompatibilityData.objects.create(bcd=new_bcd)
