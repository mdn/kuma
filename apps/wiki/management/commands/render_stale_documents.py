"""
Manually re-render stale documents
"""
import sys
import logging
from optparse import make_option

reload(sys)
sys.setdefaultencoding('utf8')

from django.conf import settings
from django.core.management.base import (BaseCommand, NoArgsCommand,
                                         CommandError)

from wiki.models import Document


class Command(BaseCommand):
    help = "Render stale wiki documents"
    option_list = BaseCommand.option_list + (
        make_option('--immediate', dest="immediate", default=False,
                    action="store_true",
                    help="Render immediately, do not use deferred queue"),
    )

    def handle(self, *args, **options):
        self.options = options
        Document.objects.render_stale(log=logging,
                                      immediate=options['immediate'])
