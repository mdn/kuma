import random
from string import letters

from django.contrib.contenttypes.models import ContentType
from django.core import mail
from django.db.models import Q

from celery.decorators import task

from notifications.models import Watch, WatchFilter, EmailUser


@task
def _fire_task(event):
    """Build and send the emails as a celery task."""
    # This is outside the Event class because @task doesn't send the `self` arg
    # implicitly, and there's no sense making it look like it does.
    connection = mail.get_connection(fail_silently=True)
    connection.open()
    for m in event._mails(event._users_watching()):
        connection.send_messages([m])


class Event(object):
    """Abstract base class for events

    An Event represents, simply, something that occurs. A Watch is a record of
    someone's interest in a certain type of Event, distinguished by
    Event.event_type.

    Fire an Event (SomeEvent.fire()) from the code that causes the interesting
    event to occur. Fire it any time the event *might* have occurred. The Event
    will determine whether conditions are right to actually send notifications;
    don't succumb to the temptation to do these tests outside the Event.

    Event subclasses can optionally represent a more limited scope of interest
    by populating the Watch.content_type field and/or adding related
    WatchFilter rows holding name/value pairs, the meaning of which is up to
    each individual subclass. NULL values are considered wildcards.

    Event subclass instances must be pickleable so they can be shuttled off to
    celery tasks.

    """
    # event_type = 'hamster modified'  # key for the event_type column
    content_type = None  # or, for example, Hamster
    filters = set()  # or, for example, set(['color', 'flavor'])

    def fire(self):
        """Asynchronously notify everyone watching the event.

        We are explicit about sending notifications; we don't just key off
        creation signals, because the receiver of a post_save signal has no
        idea what just changed, so it doesn't know which notifications to send.
        Also, we could easily send mail accidentally: for instance, during
        tests. If we want implicit event firing, we can always register a
        signal handler that calls fire().

        """
        _fire_task.delay(self)

    @classmethod
    def _validate_filters(cls, filters):
        """Raise a TypeError if `filters` contains any keys inappropriate to
        this event class."""
        for k in filters.iterkeys():
            if k not in cls.filters:
                # Mirror "unexpected keyword argument" message:
                raise TypeError("%s got an unsupported filter type '%s'" %
                                (cls.__name__, k))

    def _users_watching_by_filter(self, **filters):
        """Return an iterable of Users/EmailUsers watching the event.

        "Watching the event" means having a Watch whose event_type is
        self.event_type, whose content_type is self.content_type or NULL, and
        whose WatchFilter rows match as follows: each name/value pair given in
        `filters` must be matched by a related WatchFilter, or there must be no
        related WatchFilter having that name. If you find yourself wanting the
        lack of a particularly named WatchFilter to scuttle the match, use a
        different event_type instead.

        """
        def joins_and_params():
            """Return a concatenation of joins and params to bind to them in
            order to check a notification against all the given filters."""
            # Not a one-liner. You're welcome. :-)
            self._validate_filters(filters)
            joins, wheres, join_params, where_params = [], [], [], []
            for n, (k, v) in enumerate(filters.iteritems()):
                joins.append(
                    ' LEFT JOIN notifications_watchfilter f{n} '
                    'ON f{n}.watch_id=w.id '
                        'AND f{n}.name=%s'.format(n=n))
                join_params.append(k)
                wheres.append(' AND (f{n}.value=%s '
                              'OR f{n}.value IS NULL)'.format(n=n))
                where_params.append(v)
            return ''.join(joins), join_params, ''.join(wheres), where_params

        # Get applicable watches:
        joins, join_params, wheres, where_params = joins_and_params()
        if self.content_type:
            content_type = (' AND (w.content_type_id IS NULL '
                            'OR w.content_type_id=%s)')
            ct_param = [ContentType.objects.get_for_model(
                        self.content_type).id]
        else:
            content_type = ''
            ct_param = []
        query = (
            'SELECT w.id, w.content_type_id, w.event_type, w.user_id, '
                   'w.email, w.secret '
            'FROM notifications_watch w '
            'LEFT JOIN auth_user u ON u.id=w.user_id{left_joins} '
            'WHERE w.event_type=%s{content_type}{wheres} '
            'AND (length(w.email)>0 OR length(u.email)>0) '
            'AND w.secret IS NULL').format(
            left_joins=joins,
            content_type=content_type,
            wheres=wheres)

        # TODO: Pin to default DB.
        watches = Watch.uncached.raw(query, join_params + [self.event_type] +
                                            ct_param + where_params)

        # Yank the user out of each, or construct an anonymous user:
        for w in watches:
            # The query above guarantees us an email from either the user or
            # the watch. Some of these cases shouldn't happen, but we're
            # tolerant.
            user = w.user or EmailUser()
            if not getattr(user, 'email', ''):
                user.email = w.email
            yield user

        # Can we do "where user_id in (1, 2, 3)", grab all the real Users with
        # one query, and match them up? YAGNI for now.

        # TODO: De-dupe by email address?

    @classmethod
    def _watches_by_user(cls, user_or_email, **filters):
        """Return a QuerySet of watches having (only) the given filters as well
        as the event_type and content_type attrs of the class.

        Matched Watches may be either confirmed and unconfirmed. They may
        include duplicates if the get-then-create race condition in
        get_or_create_watch() allowed them to be created.

        If you pass an email, it will be matched against only the email
        addresses of anonymous watches. At the moment, the only integration
        point planned between anonymous and registered watches is the claiming
        of anonymous watches of the same email address on user registration
        confirmation.

        """
        # If we have trouble distinguishing subsets and such, we could store a
        # number_of_filters on the Watch.
        cls._validate_filters(filters)

        # Filter by stuff in the Watch row:
        watches = Watch.uncached.using('default').filter(
            Q(email=user_or_email) if isinstance(user_or_email, basestring)
                                   else Q(user=user_or_email),
            Q(content_type=ContentType.objects.get_for_model(cls.content_type))
                if cls.content_type
                else Q(),
            event_type=cls.event_type).extra(
                where=['(SELECT count(*) FROM notifications_watchfilter WHERE '
                       'notifications_watchfilter.watch_id='
                       'notifications_watch.id)=%s'],
                params=[len(filters)])
        # Optimization: If the subselect ends up being slow, store the number
        # of filters in each Watch row or try a GROUP BY.

        # Apply 1-to-many filters:
        for k, v in filters.iteritems():
            watches = watches.filter(filters__name=k, filters__value=v)

        return watches

    @classmethod
    # Funny arg name to reserve use of nice ones for filters
    def is_notifying(cls, user_or_email_, **filters):
        """Return whether the user/email is watching this event (either
        confirmed or unconfirmed), conditional on meeting the criteria in
        `filters`.

        Count only watches that match the given filters exactly--not ones which
        match merely a superset of them. This lets callers distinguish between
        watches which overlap in scope. Equivalently, this lets callers check
        whether notify() has been called with these arguments.

        Implementations in subclasses may take different arguments--for
        example, to assume certain filters--though most will probably just use
        this. However, subclasses should clearly document what filters they
        supports and the meaning of each.

        """
        return cls._watches_by_user(user_or_email_, **filters).exists()

    @classmethod
    def notify(cls, user_or_email_, **filters):
        """Start notifying the given user or email address when this event
        occurs and meets the criteria given in `filters`.

        Return the created (or the existing matching) Watch so you can call
        confirm() on it if you're so inclined.

        Implementations in subclasses may take different arguments; see the
        docstring of is_notifying().

        """
        # A test-for-existence-then-create race condition exists here, but it
        # doesn't matter: de-duplication on fire() and deletion of all matches
        # on delete_watch() nullify its effects.
        try:
            # Pick 1 if >1 are returned:
            watch = cls._watches_by_user(
                user_or_email_,
                **filters)[0:1].get()
        except Watch.DoesNotExist:
            create_kwargs = {}
            if cls.content_type:
                create_kwargs['content_type'] = \
                    ContentType.objects.get_for_model(cls.content_type)
            create_kwargs['email' if isinstance(user_or_email_, basestring)
                          else 'user'] = user_or_email_
            watch = Watch.objects.create(
                secret=''.join(random.choice(letters) for x in xrange(10)),
                event_type=cls.event_type,
                **create_kwargs)
            for k, v in filters.iteritems():
                # TODO: Auto-hash v into an int if it isn't one?
                WatchFilter.objects.create(watch=watch, name=k, value=v)
        return watch

    @classmethod
    def stop_notifying(cls, user_or_email_, **filters):
        """Delete all watches matching the exact user/email and filters.

        Delete both confirmed and unconfirmed watches. If duplicate watches
        exist due to the get-then-create race condition, delete them all.

        Implementations in subclasses may take different arguments; see the
        docstring of is_notifying().

        """
        cls._watches_by_user(user_or_email_, **filters).delete()

    # TODO: If GenericForeignKeys don't give us cascading deletes, make a
    # stop_notifying_all(**filters) or something. It should delete any watch of
    # the class's event_type and content_type and having filters matching each
    # of **filters. Even if there are additional filters on a watch, that watch
    # should still be deleted so we can delete, for example, any watch that
    # references a certain Question instance. To do that, factor such that you
    # can effectively call _watches_by_user() without it calling extra().

    # Subclasses should implement the following:

    def _mails(self, users):
        """Return an iterable yielding a EmailMessage to send to each User."""
        raise NotImplementedError

    def _users_watching(self):
        """Return an iterable of Users and EmailUsers watching this event.

        Default implementation returns users watching this object's event_type
        and, if defined, content_type.

        """
        return self._users_watching_by_filter()
