from __future__ import unicode_literals

from django.db.models.signals import post_delete
from django.dispatch import receiver

from kuma.wiki.models import Document
from kuma.wiki.signals import render_done

from .tasks import publish, unpublish


@receiver(render_done, sender=Document,
          dispatch_uid='api.document.render_done.publish')
def on_render_done(sender, instance, **kwargs):
    """
    A signal handler to publish the document to the document API after it
    has been rendered.
    """
    publish.delay([instance.pk])


@receiver(post_delete, sender=Document,
          dispatch_uid='api.document.post_delete.unpublish')
def on_post_delete(instance, **kwargs):
    """
    A signal handler to remove the given document from the document API after
    it has been deleted.
    """
    unpublish.delay([(instance.locale, instance.slug)])
