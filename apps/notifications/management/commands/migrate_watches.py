from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db import transaction

from forums.events import NewPostEvent, NewThreadEvent
from forums.models import Forum, Thread
from kbforums.events import (NewPostEvent as KBNewPostEvent,
                             NewThreadEvent as KBNewThreadEvent)
from kbforums.models import Thread as KBThread
from notifications.models import EventWatch
from questions.events import QuestionReplyEvent, QuestionSolvedEvent
from questions.models import Question
from wiki.events import (EditDocumentEvent, ReviewableRevisionInLocaleEvent,
                         ApproveRevisionInLocaleEvent)
from wiki.models import Document


# Not using sumo.utils.chunked so I can be smarter about calculating the
# length of a QuerySet.
def chunked(qs, n):
    """Yield successive n-sized chunks from QuerySet qs."""
    length = qs.count()
    for i in xrange(0, length, n):
        yield qs[i:i + n]


# Either a user associated with an email address or the email address.
def user_or_email(email):
    try:
        return User.objects.get(email=email)
    except User.MultipleObjectsReturned:
        # Pick the first one, note that this can't happen.
        u = User.objects.filter(email=email)
        print '%s had a duplicate email address.' % email
        return u[0]
    except User.DoesNotExist:
        return email


# Migrate instance watches for `cls` from old EventWatches to `evt`.
def migrate_instance_watches(watches, cls, evt):
    """Migrate a list of watches from a given cls to a new evt."""
    for watch in watches:
        # If there's a User with that email, use it, else use the
        # email address.
        who = user_or_email(watch.email)
        # Get the item being watched, else skip it, as stale.
        try:
            what = cls.objects.get(pk=watch.watch_id)
        except cls.DoesNotExist:
            continue
        evt.notify(who, what)


class Command(BaseCommand):
    help = 'Migrate old EventWatches into the new system.'

    def handle(self, *args, **kwargs):
        transaction.enter_transaction_management(True)

        # Map EventWatches for a specific instance and type to the new
        # InstanceEvent subclass.
        mapping = (
            ('reply', QuestionReplyEvent, Question),
            ('solution', QuestionSolvedEvent, Question),
            ('post', KBNewThreadEvent, Document),
            ('edited', EditDocumentEvent, Document),
            ('post', NewThreadEvent, Forum),
            ('reply', NewPostEvent, Thread),
            ('reply', KBNewPostEvent, KBThread),
        )
        for type, evt, model in mapping:
            ct = ContentType.objects.get_for_model(model)
            print u'Migrating %s %s to %s...' % (model, type, evt)
            watches = ct.eventwatch_set.filter(event_type=type).order_by('id')
            # Chunking because there are nearly 200k for some of these.
            for i, chunk in enumerate(chunked(watches, 2000)):
                print u'  Chunk %s' % i
                migrate_instance_watches(chunk, model, evt)
                transaction.commit()

        # Map locale-wide EventWatches to the new Event subclass.
        mapping = (
            ('approved', ApproveRevisionInLocaleEvent),
            ('ready_for_review', ReviewableRevisionInLocaleEvent),
        )
        ct = ContentType.objects.get_for_model(Document)
        for type, evt in mapping:
            print u'Migrating %s to %s...' % (type, evt)
            watches = ct.eventwatch_set.filter(event_type=type).order_by('id')
            # Not chunking because there are literally 30 of these.
            for watch in watches:
                who = user_or_email(watch.email)
                evt.notify(who, locale=watch.locale)
            transaction.commit()

        transaction.leave_transaction_management()
