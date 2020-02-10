import random

from django.conf import settings
from django.contrib.auth import get_user_model

from kuma.core.jobs import GenerationJob, KumaJob


class DocumentContributorsJob(KumaJob):
    """
    Given a wiki document returns a list of contributors that have recently
    authored revisions.

    We invalidate this when a document is saved only, not when a user account
    changes given the potential of lots of documents needing to be updated
    everytime a profile is saved. Instead we accept that some contributor links
    may be wrong until the cache item's lifetime runs out for this edge case.
    """

    lifetime = 60 * 60 * 12
    refresh_timeout = 30
    version = 2
    # Don't synchronously fetch the contributor bar but schedule a fetch
    fetch_on_miss = False

    def get(self, *args, **kwargs):
        if settings.MAINTENANCE_MODE:
            return self.empty()
        return super(DocumentContributorsJob, self).get(*args, **kwargs)

    def fetch(self, pk):
        from .models import Revision

        User = get_user_model()

        # first get a list of user ID recently authoring revisions
        recent_creator_ids = (
            Revision.objects.filter(document_id=pk)
            .order_by("-created")
            .values_list("creator_id", flat=True)
        )

        # remove duplicates, preserving order
        #   duplicates arise when a user makes multiple edits to a document
        recent_creator_ids = list(dict.fromkeys(recent_creator_ids))

        if not recent_creator_ids:
            return self.empty()

        # then return the ordered results given the ID list, MySQL only syntax
        select = {
            "ordered_ids": "FIELD(id,%s)"
            % ",".join(str(id) for id in recent_creator_ids),
        }

        return list(
            User.objects.filter(id__in=recent_creator_ids, is_active=True)
            .extra(select=select, order_by=["ordered_ids"])
            .values("id", "username", "email")
        )

    def empty(self):
        # the empty result needs to be an empty list instead of None
        return []


class DocumentCodeSampleJob(GenerationJob):
    lifetime = 60 * 60 * 12
    refresh_timeout = 60

    def fetch(self, pk, sample_name):
        from .models import Document

        document = Document.objects.get(pk=pk)
        return document.extract.code_sample(sample_name)

    def empty(self):
        return {}


class DocumentTagsJob(KumaJob):
    """
    Given a wiki document returns a list of tags.

    We invalidate this when a document is saved only.
    Longer lifetime as tags are rarely modified
    """

    refresh_timeout = 180

    @property
    def lifetime(self):
        # Spread the life time across a random
        # number of days from 1 to 10 (in units of seconds).
        # So that all the document cache do not get expired at same time
        seconds_per_day = 24 * 60 * 60
        return random.randint(1 * seconds_per_day, 10 * seconds_per_day)

    def fetch(self, pk):
        from .models import Document

        tags = (
            Document.objects.filter(id=pk)
            .exclude(tags__name=None)
            .values_list("tags__name", flat=True)
            .order_by("tags__name")
        )
        return list(tags)
