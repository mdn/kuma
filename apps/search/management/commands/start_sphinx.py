from django.core.management.base import NoArgsCommand

from search.utils import start_sphinx


class Command(NoArgsCommand):
    help = 'Start the Sphinx server.'

    def handle_noargs(self, *args, **kwargs):
        start_sphinx()
