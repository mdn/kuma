"""Extras for django-taggit

Includes:
- Handle tag namespaces (eg. tech:javascript, profile:interest:homebrewing)

TODO:
- Permissions for tag namespaces (eg. system:* is superuser-only)
- Machine tag assists
"""


from datetime import date, timedelta

from django.db import models
from django.db.models.fields import BLANK_CHOICE_DASH
from taggit.managers import _TaggableManager, TaggableManager
from taggit.models import Tag
from taggit.utils import edit_string_for_tags, require_instance_manager


class NamespacedTaggableManager(TaggableManager):
    """TaggableManager with tag namespace support"""

    # HACK: Yes, I really do want to allow tags in admin change lists
    flatchoices = None

    # HACK: This is expensive, too, but should help with list_filter in admin
    def get_choices(self, include_blank=True, blank_choice=BLANK_CHOICE_DASH):
        return [(t.id, t.name) for t in Tag.objects.all()]

    def __init__(self, *args, **kwargs):
        kwargs["manager"] = _NamespacedTaggableManager
        super(NamespacedTaggableManager, self).__init__(*args, **kwargs)


class _NamespacedTaggableManager(_TaggableManager):
    def __str__(self):
        """Return the list of tags as an editable string.
        Expensive: Does a DB query for the tags"""
        # HACK: Yes, I really do want to allow tags in admin change lists
        return edit_string_for_tags(self.all())

    def all_ns(self, namespace=None):
        """Fetch tags by namespace, or collate all into namespaces"""
        tags = self.all()

        if namespace == "":
            # Empty namespace is special - just look for absence of ':'
            return tags.exclude(name__contains=":")

        if namespace is not None:
            # Namespace requested, so generate filtered set
            results = []
            for tag in tags:
                if tag.name.startswith(namespace):
                    results.append(tag)
            return results

        # No namespace requested, so collate into namespaces
        ns_tags = {}
        for tag in tags:
            (ns, name) = self._parse_ns(tag)
            if ns not in ns_tags:
                ns_tags[ns] = [tag]
            else:
                ns_tags[ns].append(tag)
        return ns_tags

    @require_instance_manager
    def add_ns(self, namespace, *tags):
        """Add tags within a namespace"""
        ns_tags = self._ensure_ns(namespace, tags)
        super(_NamespacedTaggableManager, self).add(*ns_tags)

    @require_instance_manager
    def remove_ns(self, namespace=None, *tags):
        """Remove tags within a namespace"""
        ns_tags = self._ensure_ns(namespace, tags)
        super(_NamespacedTaggableManager, self).remove(*ns_tags)

    @require_instance_manager
    def clear_ns(self, namespace=None):
        """Clear tags within a namespace"""
        lookup_kwargs = self._lookup_kwargs()
        lookup_kwargs["tag__name__startswith"] = namespace
        self.through.objects.filter(**lookup_kwargs).delete()

    @require_instance_manager
    def set_ns(self, namespace=None, *tags):
        """Set tags within a namespace"""
        self.clear_ns(namespace)
        self.add_ns(namespace, *tags)

    def _parse_ns(self, tag):
        """Extract namespace from tag name.
        Namespace is tag name text up to and including the last
        occurrence of ':'
        """
        if ":" in tag.name:
            (ns, name) = tag.name.rsplit(":", 1)
            return ("%s:" % ns, name)
        else:
            return ("", tag.name)

    def _ensure_ns(self, namespace, tags):
        """Ensure each tag name in the list starts with the given namespace"""
        ns_tags = []
        for t in tags:
            if not t.startswith(namespace):
                t = f"{namespace}{t}"
            ns_tags.append(t)
        return ns_tags


class IPBanManager(models.Manager):
    def active(self, ip):
        return self.filter(ip=ip, deleted__isnull=True)

    def delete_old(self, days=30):
        cutoff_date = date.today() - timedelta(days=days)
        old_ip_bans = self.filter(created__lte=cutoff_date)
        old_ip_bans.delete()
