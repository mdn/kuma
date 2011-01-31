import random
from string import letters

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core import mail
from django.db.models import Q

from celery.decorators import task

from notifications.models import Watch, WatchFilter, EmailUser, multi_raw
from notifications.utils import merge


def _unique_by_email(users_and_watches):
    """Given a sequence of (User/EmailUser, Watch) pairs clustered by email
    address (which is never ''), yield from each cluster...

    (1) the first pair where the User has an email and is not anonymous, or, if
        there isn't such a user...
    (2) the first pair.

    """
    def ensure_user_has_email(user, watch):
        """Make sure the user in the user-watch pair has an email address.

        The caller guarantees us an email from either the user or the watch. If
        the passed-in user has no email, we return an EmailUser instead having
        the email address from the watch.

        """
        # Some of these cases shouldn't happen, but we're tolerant.
        if not getattr(user, 'email', ''):
            user = EmailUser(watch.email)
        return user, watch

    # TODO: Do this instead with clever SQL that somehow returns just the
    # best row for each email.

    # Email of current cluster:
    email = ''
    # Best pairs in cluster so far:
    favorite_user, favorite_watch = None, None
    for u, w in users_and_watches:
        row_email = u.email or w.email
        if email != row_email:
            if email != '':
                yield ensure_user_has_email(favorite_user, favorite_watch)
            favorite_user, favorite_watch = u, w
            email = row_email
        elif ((not favorite_user.email or isinstance(u, EmailUser))
              and u.email and not isinstance(u, EmailUser)):
            favorite_user, favorite_watch = u, w
    if favorite_user is not None:
        yield ensure_user_has_email(favorite_user, favorite_watch)


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

    def __init__(self, exclude=None):
        """Initialize event with option of excluding a user."""
        self.exclude = exclude

    def fire(self):
        """Asynchronously notify everyone watching the event.

        We are explicit about sending notifications; we don't just key off
        creation signals, because the receiver of a post_save signal has no
        idea what just changed, so it doesn't know which notifications to send.
        Also, we could easily send mail accidentally: for instance, during
        tests. If we want implicit event firing, we can always register a
        signal handler that calls fire().

        """
        # Tasks don't receive the `self` arg implicitly.
        self._fire_task.delay(self)

    @task
    def _fire_task(self):
        """Build and send the emails as a celery task."""
        connection = mail.get_connection(fail_silently=True)
        # Warning: fail_silently swallows errors thrown by the generators, too.
        connection.open()
        for m in self._mails(self._users_watching()):
            connection.send_messages([m])

    @classmethod
    def _validate_filters(cls, filters):
        """Raise a TypeError if `filters` contains any keys inappropriate to
        this event class."""
        for k in filters.iterkeys():
            if k not in cls.filters:
                # Mirror "unexpected keyword argument" message:
                raise TypeError("%s got an unsupported filter type '%s'" %
                                (cls.__name__, k))

    def _users_watching_by_filter(self, object_id=None, **filters):
        """Return an iterable of (User/EmailUser, Watch) pairs watching the
        event.

        Of multiple Users/EmailUsers having the same email address, only one is
        returned. Users are favored over EmailUsers so we are sure to be able
        to, for example, include a link to a user profile in the mail.

        "Watching the event" means having a Watch whose event_type is
        self.event_type, whose content_type is self.content_type or NULL, and
        whose WatchFilter rows match as follows: each name/value pair given in
        `filters` must be matched by a related WatchFilter, or there must be no
        related WatchFilter having that name. If you find yourself wanting the
        lack of a particularly named WatchFilter to scuttle the match, use a
        different event_type instead.

        """
        # I don't think we can use the ORM here, as there's no way to get a
        # second condition (name=whatever) into a left join. However, if we
        # were willing to have 2 subqueries run for every watch row--select
        # {are there any filters with name=x?} and select {is there a filter
        # with name=x and value=y?}--we could do it with extra(). Then we could
        # have EventUnion simple | the QuerySets together, which would avoid
        # having to merge in Python.

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
        if object_id:
            o_id = ' AND (w.object_id IS NULL OR w.object_id=%s)'
            o_id_param = [object_id]
        else:
            o_id = ''
            o_id_param = []

        # Skip self.exclude if user was passed in at init time.
        if self.exclude:
            exclude = ' AND (u.id != %s)'
            u_id_param = [self.exclude.id]
        else:
            exclude = ''
            u_id_param = []

        query = (
            'SELECT u.*, w.* '
            'FROM notifications_watch w '
            'LEFT JOIN auth_user u ON u.id=w.user_id{left_joins} '
            'WHERE w.event_type=%s{content_type}{object_id}{wheres} '
            'AND (length(w.email)>0 OR length(u.email)>0){exclude} '
            'AND w.secret IS NULL '
            'ORDER BY u.email DESC, w.email DESC').format(
            left_joins=joins,
            content_type=content_type,
            object_id=o_id,
            exclude=exclude,
            wheres=wheres)
        # IIRC, the DESC ordering was something to do with the placement of
        # NULLs. Track this down and explain it.

        return _unique_by_email(multi_raw(
            query,
            join_params + [self.event_type] + ct_param + o_id_param +
                where_params + u_id_param,
            [User, Watch]))

    @classmethod
    def _watches_belonging_to_user(cls, user_or_email, object_id=None,
                                   **filters):
        """Return a QuerySet of watches having the given user or email, having
        (only) the given filters, and having the event_type and content_type
        attrs of the class.

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
        watches = Watch.uncached.filter(
            Q(email=user_or_email) if isinstance(user_or_email, basestring)
                                   else Q(user=user_or_email),
            Q(content_type=ContentType.objects.get_for_model(cls.content_type))
                if cls.content_type
                else Q(),
            Q(object_id=object_id)
                if object_id
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
        return cls._watches_belonging_to_user(user_or_email_,
                                              **filters).exists()

    @classmethod
    def notify(cls, user_or_email_, object_id=None, **filters):
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
            watch = cls._watches_belonging_to_user(
                user_or_email_,
                **filters)[0:1].get()
        except Watch.DoesNotExist:
            create_kwargs = {}
            if cls.content_type:
                create_kwargs['content_type'] = \
                    ContentType.objects.get_for_model(cls.content_type)
            create_kwargs['email' if isinstance(user_or_email_, basestring)
                          else 'user'] = user_or_email_
            # Registered users don't need to confirm => no secret.
            # ... but anonymous users do.
            secret = (''.join(random.choice(letters) for x in xrange(10)) if
                      'email' in create_kwargs else None)
            if object_id:
                create_kwargs['object_id'] = object_id
            watch = Watch.objects.create(
                secret=secret,
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
        cls._watches_belonging_to_user(user_or_email_, **filters).delete()

    # TODO: If GenericForeignKeys don't give us cascading deletes, make a
    # stop_notifying_all(**filters) or something. It should delete any watch of
    # the class's event_type and content_type and having filters matching each
    # of **filters. Even if there are additional filters on a watch, that watch
    # should still be deleted so we can delete, for example, any watch that
    # references a certain Question instance. To do that, factor such that you
    # can effectively call _watches_belonging_to_user() without it calling
    # extra().

    # Subclasses should implement the following:

    def _mails(self, users_and_watches):
        """Return an iterable yielding an EmailMessage to send to each user.

        `users_and_watches` -- an iterable of (User or EmailUser, Watch) pairs
            where the first element is the user to send to and the second is
            the watch that indicated the user's interest in this event

        """
        # Did this instead of mail() because a common case might be sending the
        # same mail to many users. mail() would make it difficult to avoid
        # redoing the templating every time.
        raise NotImplementedError

    def _users_watching(self):
        """Return an iterable of Users and EmailUsers watching this event
        and the Watches that map them to it.

        Each yielded item is a tuple: (User or EmailUser, Watch).

        Default implementation returns users watching this object's event_type
        and, if defined, content_type.

        """
        return self._users_watching_by_filter()


class EventUnion(Event):
    """Fireable conglomeration of multiple events"""
    # Calls some private methods on events, but this and Event are good
    # friends.

    def __init__(self, *events):
        """`events` -- the events of which to take the union"""
        self.events = events

    def _mails(self, users_and_watches):
        """Default implementation fires the _mails() of my first event but may
        pass it any of my events as `self`.

        Use this default implementation when the content of each event's mail
        template is essentially the same, e.g. "This new post was made.
        Enjoy.". When the receipt of a second mail from the second event would
        add no value, this is a fine choice. If the second event's email would
        add value, you should probably fire both events independently and let
        both mails be delivered. Or, if you would like to send a single mail
        with a custom template for a batch of events, just subclass EventUnion
        and override this method.

        """
        return self.events[0]._mails(users_and_watches)

    def _users_watching(self):
        # Get a sorted iterable of user-watch pairs:
        users_and_watches = merge(*[e._users_watching() for e in self.events],
                                  key=lambda (user, watch): user.email,
                                  reverse=True)

        # Pick the best User out of each cluster of identical email addresses:
        return _unique_by_email(users_and_watches)


class InstanceEvent(Event):
    """Common case of watching a specific instance of a Model."""

    def __init__(self, instance, exclude=None):
        super(InstanceEvent, self).__init__(exclude=exclude)
        self.instance = instance

    @classmethod
    def notify(cls, user_or_email, instance):
        """Create, save, and return a Watch which fires when something
        happens to `instance`."""
        return super(InstanceEvent, cls).notify(user_or_email,
                                                object_id=instance.pk)

    @classmethod
    def stop_notifying(cls, user_or_email, instance):
        """Delete the watch created by notify."""
        super(InstanceEvent, cls).stop_notifying(user_or_email,
                                                 object_id=instance.pk)

    @classmethod
    def is_notifying(cls, user_or_email, instance):
        """Check if the watch created by notify exists."""
        return super(InstanceEvent, cls).is_notifying(user_or_email,
                                                      object_id=instance.pk)

    def _users_watching(self):
        """Return users watching this instance."""
        return self._users_watching_by_filter(object_id=self.instance.pk)
