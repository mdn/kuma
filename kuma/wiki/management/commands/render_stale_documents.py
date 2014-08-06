"""
Manually re-render stale documents
"""
import logging
from optparse import make_option

from django.core.management.base import BaseCommand
from kuma.wiki.tasks import render_stale_documents


class Command(BaseCommand):
    help = "Render stale wiki documents"
    option_list = BaseCommand.option_list + (
        make_option('--immediate', dest="immediate", default=False,
                    action="store_true",
                    help="Render immediately, do not use deferred queue"),
    )

    def handle(self, *args, **options):
        self.options = options
        render_stale_documents(log=logging, immediate=options['immediate'])
