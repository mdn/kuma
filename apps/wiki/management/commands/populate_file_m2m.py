# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging

from django.core.management.base import NoArgsCommand

from wiki.models import Document


class Command(NoArgsCommand):
    help = "Populate m2m relations for documents and their attachments"

    def handle(self, *args, **options):
        for doc in Document.objects.all():
            for attachment in doc.attachments:
                rev = attachment.current_revision
                attachment.attach(doc,
                                  rev.creator,
                                  rev.filename())
