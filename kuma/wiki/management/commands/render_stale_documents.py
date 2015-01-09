"""
Manually re-render stale documents
"""
import logging

from django.core.management.base import BaseCommand
from kuma.wiki.tasks import render_stale_documents


class Command(BaseCommand):
    help = "Render stale wiki documents"

    def handle(self, *args, **options):
        self.options = options
        render_stale_documents(log=logging)
