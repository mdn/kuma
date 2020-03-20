"""Store temporary data and interact with the database."""


import logging

from django.db import IntegrityError
from taggit.models import Tag

from kuma.users.models import User, UserBan
from kuma.wiki.constants import REDIRECT_CONTENT
from kuma.wiki.models import Document, DocumentTag, LocalizationTag, ReviewTag, Revision

logger = logging.getLogger("kuma.scraper")


class Storage(object):
    """Store temporary objects and interact with the database."""

    def __init__(self):
        self.local = {
            "document_children": {},
            "document_history": {},
            "document_metadata": {},
            "document_redirect": {},
            "revision_html": {},
        }

    def sorted_tags(self, tags):
        """
        Return tags in the desired creation order.

        Tags may include case look-alikes, such as 'Firefox' and 'firefox'.
        With taggit 0.18.0, setting both at the same time will result in an
        IntegrityError.  This returns the tags with the most capital letters
        first, so that 'Firefox' will be prioritized over 'firefox'.
        """
        tag_sort = sorted([(sum(1 for c in tag if c.islower()), tag) for tag in tags])
        return [tag for _, tag in tag_sort]

    def deduped_tags(self, tags):
        """Filter tags to remove those that only differ by case."""
        deduped = {}
        for tag in self.sorted_tags(tags):
            deduped.setdefault(tag.lower(), tag)
        return list(deduped.values())

    def safe_add_tags(self, tags, tag_type, tag_relation):
        """Add tags to object, working around duplicate tag issues."""
        for tag in self.deduped_tags(tags):
            existing_tags = tag_type.objects.filter(name=tag)
            tag_count = existing_tags.count()
            assert tag_count <= 1
            if tag_count == 1:
                dt = existing_tags.get()
            else:
                dt = tag_type.objects.create(name=tag)
            tag_relation.add(dt)

    def get_document(self, locale, slug):
        try:
            document = Document.objects.get(locale=locale, slug=slug)
        except Document.DoesNotExist:
            return None
        else:
            return document

    def save_document(self, data):
        doc_data = data.copy()
        locale = doc_data.pop("locale")
        slug = doc_data.pop("slug")
        doc_id = doc_data.pop("id", None)
        tags = doc_data.pop("tags", [])
        redirect_to = doc_data.pop("redirect_to", None)

        attempt = 0
        document = None
        while attempt < 2 and not document:
            # With ca/docs/Project:Quant_a, no document is found with the
            # locales, slug or ID, but an IntegrityError is raised due to an
            # ID collision when created. It will work as an update on the
            # second pass.

            attempt += 1
            try:
                document = Document.objects.get(locale=locale, slug=slug)
            except Document.DoesNotExist:
                if doc_id and not Document.objects.filter(id=doc_id).exists():
                    doc_data["id"] = doc_id
                try:
                    document = Document.objects.create(
                        locale=locale, slug=slug, **doc_data
                    )
                except IntegrityError as error:
                    logger.warning(
                        'On locale "%s", slug "%s", got error %s', locale, slug, error
                    )
                    doc_data.pop("id", None)
            else:
                for name, value in doc_data.items():
                    setattr(document, name, value)
                if redirect_to:
                    document.is_redirect = True
                    document.html = REDIRECT_CONTENT % {
                        "href": redirect_to,
                        "title": document.title,
                    }
                document.save()
        assert document is not None
        self.safe_add_tags(tags, DocumentTag, document.tags)

        Document.objects.filter(pk=document.pk).update(json=None)

    def get_document_metadata(self, locale, slug):
        return self.local["document_metadata"].get((locale, slug), None)

    def save_document_metadata(self, locale, slug, data):
        self.local["document_metadata"][(locale, slug)] = data

    def get_document_history(self, locale, slug):
        return self.local["document_history"].get((locale, slug), None)

    def save_document_history(self, locale, slug, data):
        self.local["document_history"][(locale, slug)] = data

    def get_document_redirect(self, locale, slug):
        return self.local["document_redirect"].get((locale, slug), None)

    def save_document_redirect(self, locale, slug, data):
        self.local["document_redirect"][(locale, slug)] = data

    def get_document_children(self, locale, slug):
        return self.local["document_children"].get((locale, slug), None)

    def save_document_children(self, locale, slug, data):
        self.local["document_children"][(locale, slug)] = data

    def get_revision(self, revision_id):
        try:
            revision = Revision.objects.get(id=revision_id)
        except Revision.DoesNotExist:
            return None
        else:
            return revision

    def save_revision(self, data):
        revision_id = data.pop("id")
        is_current = data.pop("is_current")
        creator = data.pop("creator")
        document = data.pop("document")
        tags = data.pop("tags")
        review_tags = data.pop("review_tags", [])
        localization_tags = data.pop("localization_tags", [])
        revision, created = Revision.objects.get_or_create(
            id=revision_id,
            defaults={
                "creator": creator,
                "document": document,
                "is_approved": False,  # Don't make current rev
            },
        )
        for name, value in data.items():
            setattr(revision, name, value)
        revision.content = revision.content or ""

        # Manually add tags, to avoid issues with adding two 'duplicate'
        #  tags, like 'Firefox' and 'firefox'
        deduped_tags = self.deduped_tags(tags)
        new_tags = []
        for tag in deduped_tags:
            try:
                tag = DocumentTag.objects.get(name=tag)
            except DocumentTag.DoesNotExist:
                tag = DocumentTag.objects.create(name=tag)
            new_tags.append('"%s"' % tag.name)
        if new_tags:
            revision.tags = " ".join(new_tags)

        # is_approved will update the document, avoid for old revisions
        revision.is_approved = is_current
        revision.save()

        # Add review, localization tags
        for tag_name in review_tags:
            tag, created = ReviewTag.objects.get_or_create(
                name=tag_name, defaults={"slug": tag_name}
            )
            revision.review_tags.add(tag)
        for tag_name in localization_tags:
            tag, created = LocalizationTag.objects.get_or_create(
                name=tag_name, defaults={"slug": tag_name}
            )
            revision.localization_tags.add(tag)

        # Approve old revisions w/o making them current
        if not revision.is_approved:
            Revision.objects.filter(id=revision.id).update(is_approved=True)

    def get_revision_html(self, path):
        return self.local["revision_html"].get((path), None)

    def save_revision_html(self, path, data):
        self.local["revision_html"][path] = data

    def get_user(self, username):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return None
        else:
            return user

    def save_user(self, data):
        username = data.pop("username")
        banned = data.pop("banned", False)
        user, created = User.objects.get_or_create(username=username)
        for name, value in data.items():
            if name in ("interest", "expertise"):
                tags = ["profile:%s:%s" % (name, tag) for tag in value]
                self.safe_add_tags(tags, Tag, user.tags)
            else:
                setattr(user, name, value)
        user.save()

        if banned:
            ban, ban_created = UserBan.objects.get_or_create(
                user=user, defaults={"by": user, "reason": "Ban detected by scraper"}
            )
