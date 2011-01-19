from itertools import count

from django.core import mail
from django.core.mail import EmailMessage


class Event(object):
    """Abstract base class for events

    An event represents, simply, something that occurs. A Watch is a record of
    someone's interest in a certain type of event, distinguished by
    Event.event_type.

    Fire an Event (SomeEvent.fire()) from the code that causes the interesting
    event to occur. Fire it any time the event *might* have occurred. The Event
    will determine whether conditions are right to actually send notifications;
    don't succumb to the temptation to do these tests outside the Event.

    Event subclasses can optionally represent a more limited scope of interest
    by populating the Watch.content_type field and/or adding related
    WatchFilter rows holding name/value pairs, the meaning of which is up to
    each individual subclass. NULL values are considered wildcards.

    """
    # event_type = 'hamster modified'  # Key for the event_type column.
    # content_type = Hamster  # optional

    # Mappings from _watches_core kwarg names to WatchFilter.name values:
    filters = {}  # or, for example, {'color': 'COLR'}

    def fire(self):
        """Notify everyone watching the question--except the asker.

        We are explicit about sending notifications; don't just key off
        creation signals, because the receiver of a post_save signal has no
        idea what just changed, so it doesn't know which notifications to send.
        Also, we could easily send mail accidentally: for instance, during
        tests. If we want implicit event firing, we can always register a
        signal handler that calls fire().

        """
        # TODO: Move offthread.
        connection = mail.get_connection()
        connection.send_messages(self._build_mails(self._watches()))
        # TODO: Pass fail_silently or whatever.

    def _watches_core(self, **filters):
        """Return an iterable of Users/AnonymousUsers watching the event.

        "Watching the event" means having a Watch whose content_type is
        self.content_type or NULL and WatchFilter rows that match as follows:
        every name/value pair given in `filters` must be matched by a related
        WatchFilter, or there must be no related WatchFilter having that name.

        """
        def _joins_and_params():
            """Return a concatenation of joins and params to bind to them in
            order to check a notification against all the given filters."""
            # Not a one-liner. You're welcome. :-)
            joins = []
            params = []
            n = count()
            for k, v in filters.iteritems():
                if k in self.filters:
                    joins.append(
                        ' LEFT JOIN notifications_watchfilter f{n} '
                        'ON f{n}.watch_id=w.id '
                            'AND f{n}.name=%s AND f{n}.value=%s'.format(
                        n=n.next()))
                    params.extend((k, v))
            return ''.join(joins), params

        # Get applicable watches:
        joins, left_params = _joins_and_params()
        if self.content_type:
            content_type = ' AND (w.content_type IS NULL OR w.content_type=%s)'
            ct_param = [self.content_type]
        else:
            content_type = ''
            ct_param = []
        query = (
            'SELECT w.content_type, w.event_type, w.user, w.email, w.secret '
            'FROM notifications_watch w '
            'LEFT JOIN auth_user u ON u.id=w.user_id{left_joins} '
            'WHERE w.event_type=%s{content_type} '
            'AND (length(w.email)>0 OR length(u.email)>0)').format(
            left_joins=joins(),
            content_type=content_type)
        watches = Watch.objects.raw(query, left_params + [self.event_type] +
                                           ct_param)

        # Yank the user out of each, or construct an anonymous user:
        for w in watches:
            # The query above guarantees us an email from either the user or
            # the watch. Some of these cases shouldn't happen, but we're
            # tolerant.
            user = w.user or AnonymousUser()
            if not getattr(user, 'email', ''):
                user.email = w.email
            yield user

        # Can we do "where user_id in (1, 2, 3)", grab all the real Users with
        # one query, and match them up somehow? YAGNI for now.

        # TODO: De-dupe by email address?

    def _build_mails(self, users):
        """Return an iterable of EmailMessages to send to each User."""
        raise NotImplementedError

    def _watches(self):
        """Return an iterable of Users and AnonymousUsers watching this event.

        Take care not to hash or compare AnonymousUsers; they all compare
        equal.

        """
        raise NotImplementedError

    # Recommended for subclasses:
    # @classmethod
    # def watch(cls, ...)
    #     """Create, save, and return a watch on the given criteria."""

    # Rather than a symmetric unwatch(), I'm thinking of just having some kind
    # of get_watch() thing which would return a Watch. You could then either
    # use its knowledge to, for example, test whether a user is watching
    # something, or call delete() on it like a normal model object.
