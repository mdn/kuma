# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

# From kuma/wiki/models.py, DocumentSpamAttempt
NEEDS_REVIEW = 0
REVIEW_UNAVAILABLE = 3


def set_review_unavailable(apps, schema_editor):
    """For historic DocumentSpamAttempt, set to REVIEW_UNAVAILABLE."""
    DocumentSpamAttempt = apps.get_model('wiki', 'DocumentSpamAttempt')
    to_set = DocumentSpamAttempt.objects.filter(data__isnull=True,
                                                review=NEEDS_REVIEW)
    to_set.update(review=REVIEW_UNAVAILABLE)


def clear_review(apps, schema_editor):
    """Revert REVIEW_UNAVAILABLE back to NEEDS_REVIEW."""
    DocumentSpamAttempt = apps.get_model('wiki', 'DocumentSpamAttempt')
    to_clear = DocumentSpamAttempt.objects.filter(review=REVIEW_UNAVAILABLE)
    to_clear.update(review=NEEDS_REVIEW)


class Migration(migrations.Migration):

    dependencies = [
        ('wiki', '0024_add_review_to_documentspamattempt'),
    ]

    operations = [
        migrations.RunPython(set_review_unavailable, clear_review)
    ]
