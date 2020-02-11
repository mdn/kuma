from datetime import date, datetime, timedelta

from django.db import models
from django_mysql.models import QuerySet


class BaseDocumentManager(models.Manager):
    """Manager for Documents, assists for queries"""

    def get_queryset(self):
        return QuerySet(self.model)

    def get_by_natural_key(self, locale, slug):
        return self.get(locale=locale, slug=slug)

    def get_by_stale_rendering(self):
        """Find documents whose renderings have gone stale"""
        return self.exclude(render_expires__isnull=True).filter(
            render_expires__lte=datetime.now()
        )

    def filter_for_list(
        self,
        locale=None,
        tag=None,
        tag_name=None,
        errors=None,
        noparent=None,
        toplevel=None,
    ):
        """
        Returns a filtered queryset for a list of names and urls.
        """

        docs = (
            self.filter(is_redirect=False)
            .exclude(slug__startswith="User:")
            .exclude(slug__startswith="Talk:")
            .exclude(slug__startswith="User_talk:")
            .exclude(slug__startswith="Template_talk:")
            .exclude(slug__startswith="Project_talk:")
            .exclude(slug__startswith="Experiment:")
            .order_by("slug")
        )
        if locale:
            docs = docs.filter(locale=locale)
        if tag:
            docs = docs.filter(tags__in=[tag])
        if tag_name:
            docs = docs.filter(tags__name=tag_name)
        if errors:
            docs = docs.exclude(rendered_errors__isnull=True).exclude(
                rendered_errors__exact="[]"
            )
        if noparent:
            # List translated pages without English source associated
            docs = docs.filter(parent__isnull=True)
        if toplevel:
            docs = docs.filter(parent_topic__isnull=True)

        # Only include fields needed for a list of links to docs
        docs = docs.only("id", "locale", "slug", "deleted", "title", "summary_text")
        return docs

    def _filter_by_revision_flag(
        self, revision_tag, locale=None, tag=None, tag_name=None
    ):
        """Filter documents by moderator flags on the current revision."""
        docs = self.filter_for_list(locale=locale)
        docs = docs.exclude(slug__startswith="Archive/")
        filter_name = "current_revision__%s_tags__" % revision_tag
        if tag_name:
            docs = docs.filter(**{filter_name + "name": tag_name})
        elif tag:
            docs = docs.filter(**{filter_name + "in": [tag]})
        else:
            docs = docs.filter(**{filter_name + "name__isnull": False})
        return docs.distinct()

    def filter_for_review(self, locale=None, tag=None, tag_name=None):
        """Filter for documents with current revision flagged for review"""
        return self._filter_by_revision_flag("review", locale, tag, tag_name)

    def filter_with_localization_tag(self, locale=None, tag=None, tag_name=None):
        """Filter for documents with a localization tag on current revision"""
        return self._filter_by_revision_flag("localization", locale, tag, tag_name)


class DocumentManager(BaseDocumentManager):
    """
    The actual manager, which filters to show only non-deleted pages.
    """

    def get_queryset(self):
        return super(DocumentManager, self).get_queryset().filter(deleted=False)


class DeletedDocumentManager(BaseDocumentManager):
    """
    Specialized manager for working with deleted pages.
    """

    def get_queryset(self):
        return super(DeletedDocumentManager, self).get_queryset().filter(deleted=True)


class AllDocumentManager(BaseDocumentManager):
    """
    Similar to DocumentAdminManager class but more explicit in its name.
    Use this when you don't want *any* filtering by 'deleted'.
    """


class DocumentAdminManager(BaseDocumentManager):
    """
    A manager used only in the admin site, which does not perform any
    filtering based on deleted status.
    """


class TaggedDocumentManager(models.Manager):
    def get_queryset(self):
        base_qs = super(TaggedDocumentManager, self).get_queryset()
        return base_qs.filter(content_object__deleted=False)


class RevisionIPManager(models.Manager):
    def delete_old(self, days=30):
        cutoff_date = date.today() - timedelta(days=days)
        old_rev_ips = self.filter(revision__created__lte=cutoff_date)
        old_rev_ips.delete()

    def log(self, revision, headers, data):
        """
        Records the IP and some more data for the given revision and the
        request headers.
        """
        self.create(
            revision=revision,
            ip=headers.get("REMOTE_ADDR"),
            user_agent=headers.get("HTTP_USER_AGENT", ""),
            referrer=headers.get("HTTP_REFERER", ""),
            data=data,
        )
