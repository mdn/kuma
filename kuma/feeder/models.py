from django.db import models
from django.utils.functional import cached_property

import jsonpickle

from kuma.core.sections import SECTIONS_TWITTER, SECTIONS_UPDATES


class BundleManager(models.Manager):
    """Custom manager for bundles."""

    def recent_entries(self, bundles):
        """Most recent entries."""
        if isinstance(bundles, basestring):
            # Single bundle.
            return Entry.objects.filter(feed__bundles__shortname=bundles)
        else:
            # Sequence of bundles.
            return Entry.objects.filter(
                feed__bundles__shortname__in=bundles)


class Bundle(models.Model):
    """A bundle of several feeds. A feed can be in several (or no) bundles."""

    shortname = models.SlugField(
        help_text='Short name to find this bundle by.', unique=True)
    feeds = models.ManyToManyField('feeder.Feed', related_name='bundles',
                                   blank=True)

    objects = BundleManager()

    def __unicode__(self):
        return self.shortname


class Feed(models.Model):
    """A feed holds the metadata of an RSS feed."""

    shortname = models.SlugField(
        help_text='Short name to find this feed by.', unique=True)

    title = models.CharField(max_length=140)
    url = models.CharField(max_length=2048)

    # HTTP Headers
    etag = models.CharField(max_length=140)
    last_modified = models.DateTimeField()

    # If a feed has (severe) issues, it will be disabled
    enabled = models.BooleanField(default=True)
    disabled_reason = models.CharField(max_length=2048, blank=True)

    keep = models.PositiveIntegerField(
        default=0, help_text=('Discard all but this amount of entries. 0 == '
                              'do not discard.'))

    created = models.DateTimeField(
        auto_now_add=True, verbose_name='Created On')
    updated = models.DateTimeField(
        auto_now=True, verbose_name='Last Modified')

    def __unicode__(self):
        return self.shortname

    def delete_old_entries(self):
        """Delete entries that exceed the amount we want to keep."""
        if not self.keep > 0:
            return

        to_delete = self.entries.order_by('-last_published')[self.keep:]
        for item in to_delete:
            # This doesn't perform extremely well, but it's what we have to do
            # to keep exactly `n` entries around, as LIMIT is invalid in a
            # DELETE statement.
            item.delete()


class Entry(models.Model):
    """An entry is an item representing feed content."""

    feed = models.ForeignKey(Feed, related_name='entries')
    guid = models.CharField(max_length=255)

    raw = models.TextField()

    visible = models.BooleanField(default=True)

    # Feed entry updated field
    last_published = models.DateTimeField()

    created = models.DateTimeField(
        auto_now_add=True, verbose_name='Created On')
    updated = models.DateTimeField(
        auto_now=True, verbose_name='Last Modified')

    class Meta:
        ordering = ['-last_published']
        unique_together = ('feed', 'guid')
        verbose_name_plural = 'Entries'

    def __unicode__(self):
        return '%s: %s' % (self.feed.shortname, self.guid)

    @cached_property
    def parsed(self):
        """Unpickled feed data."""
        return jsonpickle.decode(self.raw)

    @cached_property
    def section(self):
        """The section this entry is associated with."""
        try:
            bundle = self.feed.bundles.all()[0].shortname
        except IndexError:
            return None
        return SECTIONS_TWITTER.get(bundle, SECTIONS_UPDATES.get(
            bundle, None))
