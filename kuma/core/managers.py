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
from django.contrib.auth.models import AnonymousUser

from taggit.managers import TaggableManager, _TaggableManager
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
        kwargs['manager'] = _NamespacedTaggableManager
        super(NamespacedTaggableManager, self).__init__(*args, **kwargs)


class _NamespacedTaggableManager(_TaggableManager):

    def __unicode__(self):
        """Return the list of tags as an editable string.
        Expensive: Does a DB query for the tags"""
        # HACK: Yes, I really do want to allow tags in admin change lists
        return edit_string_for_tags(self.all())

    def all_ns(self, namespace=None):
        """Fetch tags by namespace, or collate all into namespaces"""
        tags = self.all()

        if namespace == '':
            # Empty namespace is special - just look for absence of ':'
            return tags.exclude(name__contains=':')

        if namespace is not None:
            # Namespace requested, so generate filtered set
            # TODO: Do this in the DB query? Might not be worth it.
            #
            # On databases with case-insensitive collation, we can end
            # up with duplicate tags (the same tag, differing only by
            # case, like 'javascript' and 'JavaScript') in some
            # cases. The most common instance of this is user
            # tags, which are coerced to lowercase on save to avoid
            # the problem, but because there are a large number of
            # these duplicates already existing, we do a quick filter
            # here to ensure we don't return a bunch of dupes that
            # differ only by case.
            seen = []
            results = []
            for tag in tags:
                if tag.name.startswith(namespace) and tag.name.lower() not in seen:
                    seen.append(tag.name.lower())
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
        lookup_kwargs['tag__name__startswith'] = namespace
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
        if (':' in tag.name):
            (ns, name) = tag.name.rsplit(':', 1)
            return ('%s:' % ns, name)
        else:
            return ('', tag.name)

    def _ensure_ns(self, namespace, tags):
        """Ensure each tag name in the list starts with the given namespace"""
        ns_tags = []
        for t in tags:
            if not t.startswith(namespace):
                t = '%s%s' % (namespace, t)
            ns_tags.append(t)
        return ns_tags


def parse_tag_namespaces(tag_list):
    """Parse a list of tags out into a dict of lists by namespace"""
    namespaces = {}
    for tag in tag_list:
        ns = (':' in tag) and ('%s:' % tag.rsplit(':', 1)[0]) or ''
        if ns not in namespaces:
            namespaces[ns] = []
        namespaces[ns].append(tag)
    return namespaces


def allows_tag_namespace_for(model_obj, ns, user):
    """Decide whether a tag namespace is editable by a user"""
    if user.is_staff or user.is_superuser:
        # Staff / superuser can manage any tag namespace
        return True
    if not ns.startswith('system:'):
        return True
    return False


def resolve_allowed_tags(model_obj, tags_curr, tags_new,
                         request_user=AnonymousUser):
    """Given a new set of tags and a user, build a list of allowed new tags
    with changes accepted only for namespaces where editing is allowed for
    the user. For disallowed namespaces, this object's current tag set will
    be imposed.

    No changes are made; the new tag list is just returned.
    """
    # Produce namespaced sets of current and incoming new tags.
    ns_tags_curr = parse_tag_namespaces(tags_curr)
    ns_tags_new = parse_tag_namespaces(tags_new)

    # Produce a union of all namespaces, current and new tag set
    all_ns = set(ns_tags_curr.keys() + ns_tags_new.keys())

    # Assemble accepted changed tag set according to permissions
    tags_out = []
    for ns in all_ns:
        if model_obj.allows_tag_namespace_for(ns, request_user):
            # If the user is allowed this namespace, apply changes by
            # accepting new tags or lack thereof.
            if ns in ns_tags_new:
                tags_out.extend(ns_tags_new[ns])
        elif ns in ns_tags_curr:
            # If the user is not allowed this namespace, carry over
            # existing tags or lack thereof
            tags_out.extend(ns_tags_curr[ns])

    return tags_out


class IPBanManager(models.Manager):
    def active(self, ip):
        return self.filter(ip=ip, deleted__isnull=True)

    def delete_old(self, days=30):
        cutoff_date = date.today() - timedelta(days=days)
        old_ip_bans = self.filter(created__lte=cutoff_date)
        old_ip_bans.delete()
