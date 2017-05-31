"""Store temporary data and interact with the database."""
from collections import OrderedDict
import logging

from taggit.models import Tag

from kuma.users.models import User, UserBan

logger = logging.getLogger('kuma.scraper')


class Storage(object):
    """Store temporary objects and interact with the database."""

    def sorted_tags(self, tags):
        """
        Return tags in the desired creation order.

        Tags may include case look-alikes, such as 'Firefox' and 'firefox'.
        With taggit 0.18.0, setting both at the same time will result in an
        IntegrityError.  This returns the tags with the most capital letters
        first, so that 'Firefox' will be prioritized over 'firefox'.
        """
        tag_sort = sorted([(sum(1 for c in tag if c.islower()), tag)
                           for tag in tags])
        return [tag for _, tag in tag_sort]

    def deduped_tags(self, tags):
        """Filter tags to remove those that only differ by case."""
        deduped = OrderedDict()
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

    def get_user(self, username):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return None
        else:
            return user

    def save_user(self, data):
        username = data.pop('username')
        banned = data.pop('banned', False)
        user, created = User.objects.get_or_create(username=username)
        for name, value in data.items():
            if name in ('interest', 'expertise'):
                tags = ['profile:%s:%s' % (name, tag) for tag in value]
                self.safe_add_tags(tags, Tag, user.tags)
            else:
                setattr(user, name, value)
        user.save()

        if banned:
            ban, ban_created = UserBan.objects.get_or_create(
                user=user,
                defaults={'by': user, 'reason': 'Ban detected by scraper'})
