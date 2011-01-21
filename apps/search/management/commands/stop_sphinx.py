from django.core.management.base import NoArgsCommand

from search.utils import stop_sphinx


class Command(NoArgsCommand):
    help = 'Stop the Sphinx server.'

    def handle_noargs(self, *args, **kwargs):
        stop_sphinx()
