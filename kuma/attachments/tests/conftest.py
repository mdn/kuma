import datetime

import pytest
from django.core.files.base import ContentFile

from kuma.attachments.models import Attachment, AttachmentRevision


@pytest.fixture
def file_attachment(db, wiki_user):
    file_id = 97
    filename = "test.txt"
    title = "Test text file"

    attachment = Attachment(title=title, mindtouch_attachment_id=file_id)
    attachment.save()
    revision = AttachmentRevision(
        title=title,
        is_approved=True,
        attachment=attachment,
        mime_type="text/plain",
        description="Initial upload",
        created=datetime.datetime.now(),
    )
    revision.creator = wiki_user
    revision.file.save(filename, ContentFile(b"This is only a test."))
    revision.make_current()
    return dict(
        attachment=attachment,
        file=dict(id=file_id, name=filename),
    )
