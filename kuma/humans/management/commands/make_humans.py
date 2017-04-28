from django.core.management.base import NoArgsCommand

from kuma.humans.tasks import humans_txt


class Command(NoArgsCommand):
    help = "Create a new MDN contributors file (humans.txt)"

    def handle(self, *args, **options):
        humans_txt()
