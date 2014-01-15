import random
from smtplib import SMTPException
from string import letters

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core import mail
from django.db.models import Q

from celery.task import task

from notifications.models import Watch, WatchFilter, EmailUser, multi_raw
from notifications.utils import merge, hash_to_unsigned


class ActivationRequestFailed(Exception):
    """Raised when activation request fails, e.g. if email could not be sent"""
    def __init__(self, msgs):
        self.msgs = msgs


def _unique_by_email(users_and_watches):
    """Given a sequence of (User/EmailUser, Watch) pairs clustered by email
    address (which is never ''), yield from each cluster...

    (1) the first pair where the User has an email and is not anonymous, or, if
        there isn't such a user...
    (2) the first pair.

    Compares email addresses case-insensitively.

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
        if email.lower() != row_email.lower():
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

    def fire(self, exclude=None):
        """Asynchronously notify everyone watching the event.

        We are explicit about sending notifications; we don't just key off
        creation signals, because the receiver of a post_save signal has no
        idea what just changed, so it doesn't know which notifications to send.
        Also, we could easily send mail accidentally: for instance, during
        tests. If we want implicit event firing, we can always register a
        signal handler that calls fire().

        If a saved user is passed in as `exclude`, that user will not be
        notified, though anonymous notifications having the same email address
        may still be sent.

        """
        # Tasks don't receive the `self` arg implicitly.
        self._fire_task.delay(self, exclude=exclude)

    @task
    def _fire_task(self, exclude=None):
        """Build and send the emails as a celery task."""
        connection = mail.get_connection(fail_silently=True)
        # Warning: fail_silently swallows errors thrown by the generators, too.
        connection.open()
        for m in self._mails(self._users_watching(exclude=exclude)):
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

    def _users_watching_by_filter(self, object_id=None, exclude=None,
                                  **filters):
        """Return an iterable of (User/EmailUser, Watch) pairs watching the
        event.

        Of multiple Users/EmailUsers having the same email address, only one is
        returned. Users are favored over EmailUsers so we are sure to be able
        to, for example, include a link to a user profile in the mail.

        "Watching the event" means having a Watch whose event_type is
        self.event_type, whose content_type is self.content_type or NULL, whose
        object_id is `object_id` or NULL, and whose WatchFilter rows match as
        follows: each name/value pair given in `filters` must be matched by a
        related WatchFilter, or there must be no related WatchFilter having
        that name. If you find yourself wanting the lack of a particularly
        named WatchFilter to scuttle the match, use a different event_type
        instead.

        If a saved user is passed in as `exclude`, that user will never be
        returned, though anonymous watches having the same email address may.

        """
        # I don't think we can use the ORM here, as there's no way to get a
        # second condition (name=whatever) into a left join. However, if we
        # were willing to have 2 subqueries run for every watch row--select
        # {are there any filters with name=x?} and select {is there a filter
        # with name=x and value=y?}--we could do it with extra(). Then we could
        # have EventUnion simple | the QuerySets together, which would avoid
        # having to merge in Python.

        def filter_conditions():
            """Return joins, WHERE conditions, and params to bind to them in
            order to check a notification against all the given filters."""
            # Not a one-liner. You're welcome. :-)
            self._validate_filters(filters)
            joins, wheres, join_params, where_params = [], [], [], []
            for n, (k, v) in enumerate(filters.iteritems()):
                joins.append(
                    'LEFT JOIN notifications_watchfilter f{n} '
                    'ON f{n}.watch_id=w.id '
                        'AND f{n}.name=%s'.format(n=n))
                join_params.append(k)
                wheres.append('(f{n}.value=%s '
                              'OR f{n}.value IS NULL)'.format(n=n))
                where_params.append(hash_to_unsigned(v))
            return joins, wheres, join_params + where_params

        # Apply watchfilter constraints:
        joins, wheres, params = filter_conditions()

        # Start off with event_type, which is always a constraint. These go in
        # the `wheres` list to guarantee that the AND after the {wheres}
        # substitution in the query is okay.
        wheres.append('w.event_type=%s')
        params.append(self.event_type)

        # Constrain on other 1-to-1 attributes:
        if self.content_type:
            wheres.append('(w.content_type_id IS NULL '
                          'OR w.content_type_id=%s)')
            params.append(ContentType.objects.get_for_model(
                          self.content_type).id)
        if object_id:
            wheres.append('(w.object_id IS NULL OR w.object_id=%s)')
            params.append(object_id)
        if exclude:
            if exclude.id:  # Don't try excluding unsaved Users.
                wheres.append('(u.id IS NULL OR u.id!=%s)')
                params.append(exclude.id)
            else:
                raise ValueError("Can't exclude an unsaved User.")

        query = (
            'SELECT u.*, w.* '
            'FROM notifications_watch w '
            'LEFT JOIN auth_user u ON u.id=w.user_id {joins} '
            'WHERE {wheres} '
            'AND (length(w.email)>0 OR length(u.email)>0) '
            'AND w.is_active '
            'ORDER BY u.email DESC, w.email DESC').format(
            joins=' '.join(joins),
            wheres=' AND '.join(wheres))
        # IIRC, the DESC ordering was something to do with the placement of
        # NULLs. Track this down and explain it.

        return _unique_by_email(multi_raw(query, params, [User, Watch]))

    @classmethod
    def _watches_belonging_to_user(cls, user_or_email, object_id=None,
                                   **filters):
        """Return a QuerySet of watches having the given user or email, having
        (only) the given filters, and having the event_type and content_type
        attrs of the class.

        Matched Watches may be either confirmed and unconfirmed. They may
        include duplicates if the get-then-create race condition in notify()
        allowed them to be created.

        If you pass an email, it will be matched against only the email
        addresses of anonymous watches. At the moment, the only integration
        point planned between anonymous and registered watches is the claiming
        of anonymous watches of the same email address on user registration
        confirmation.

        If you pass the AnonymousUser, this will return an empty QuerySet.

        """
        # If we have trouble distinguishing subsets and such, we could store a
        # number_of_filters on the Watch.
        cls._validate_filters(filters)

        if isinstance(user_or_email, basestring):
            user_condition = Q(email=user_or_email)
        elif not user_or_email.is_anonymous():
            user_condition = Q(user=user_or_email)
        else:
            return Watch.objects.none()

        # Filter by stuff in the Watch row:
        watches = Watch.objects.filter(
            user_condition,
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
            watches = watches.filter(filters__name=k,
                                     filters__value=hash_to_unsigned(v))

        return watches

    @classmethod
    # Funny arg name to reserve use of nice ones for filters
    def is_notifying(cls, user_or_email_, object_id=None, **filters):
        """Return whether the user/email is watching this event (either
        active or inactive watches), conditional on meeting the criteria in
        `filters`.

        Count only watches that match the given filters exactly--not ones which
        match merely a superset of them. This lets callers distinguish between
        watches which overlap in scope. Equivalently, this lets callers check
        whether notify() has been called with these arguments.

        Implementations in subclasses may take different arguments--for
        example, to assume certain filters--though most will probably just use
        this. However, subclasses should clearly document what filters they
        supports and the meaning of each.

        Passing this an AnonymousUser always returns False. This means you can
        always pass it request.user in a view and get a sensible response.

        """
        return cls._watches_belonging_to_user(user_or_email_,
                                              object_id=object_id,
                                              **filters).exists()

    @classmethod
    def notify(cls, user_or_email_, object_id=None, **filters):
        """Start notifying the given user or email address when this event
        occurs and meets the criteria given in `filters`.

        Return the created (or the existing matching) Watch so you can call
        activate() on it if you're so inclined.

        Implementations in subclasses may take different arguments; see the
        docstring of is_notifying().

        Send an activation email if an anonymous watch is created and
        settings.CONFIRM_ANONYMOUS_WATCHES = True. If the activation request
        fails, raise a ActivationRequestFailed exception.

        Calling notify() twice for an anonymous user will send the email
        each time.

        """
        # A test-for-existence-then-create race condition exists here, but it
        # doesn't matter: de-duplication on fire() and deletion of all matches
        # on stop_notifying() nullify its effects.
        try:
            # Pick 1 if >1 are returned:
            watch = cls._watches_belonging_to_user(
                user_or_email_,
                object_id=object_id,
                **filters)[0:1].get()
        except Watch.DoesNotExist:
            create_kwargs = {}
            if cls.content_type:
                create_kwargs['content_type'] = \
                    ContentType.objects.get_for_model(cls.content_type)
            create_kwargs['email' if isinstance(user_or_email_, basestring)
                          else 'user'] = user_or_email_
            secret = ''.join(random.choice(letters) for x in xrange(10))
            # Registered users don't need to confirm, but anonymous users do.
            is_active = ('user' in create_kwargs or
                          not settings.CONFIRM_ANONYMOUS_WATCHES)
            if object_id:
                create_kwargs['object_id'] = object_id
            watch = Watch.objects.create(
                secret=secret,
                is_active=is_active,
                event_type=cls.event_type,
                **create_kwargs)
            for k, v in filters.iteritems():
                WatchFilter.objects.create(watch=watch, name=k,
                                           value=hash_to_unsigned(v))
        # Send email for inactive watches.
        if not watch.is_active:
            email = watch.user.email if watch.user else watch.email
            message = cls._activation_email(watch, email)
            try:
                message.send()
            except SMTPException, e:
                watch.delete()
                raise ActivationRequestFailed(e.recipients)
        return watch

    @classmethod
    def stop_notifying(cls, user_or_email_, **filters):
        """Delete all watches matching the exact user/email and filters.

        Delete both active and inactive watches. If duplicate watches
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

    def _users_watching(self, **kwargs):
        """Return an iterable of Users and EmailUsers watching this event
        and the Watches that map them to it.

        Each yielded item is a tuple: (User or EmailUser, Watch).

        Default implementation returns users watching this object's event_type
        and, if defined, content_type.

        """
        return self._users_watching_by_filter(**kwargs)

    @classmethod
    def _activation_email(cls, watch, email):
        """Return an EmailMessage to send to anonymous watchers.

        They are expected to follow the activation URL sent in the email to
        activate their watch, so you should include at least that.

        """
        # TODO: basic implementation.
        return mail.EmailMessage('TODO', 'Activate!',
                                 settings.NOTIFICATIONS_FROM_ADDRESS,
                                 [email])

    @classmethod
    def _activation_url(cls, watch):
        """Return a URL pointing to the watch activation.

        TODO: provide generic implementation of this before liberating.
        Generic implementation could involve a setting to the default reverse()
        path, e.g. 'notifications.activate_watch'.

        """
        raise NotImplementedError

    @classmethod
    def watch_description(cls, watch):
        """Return a description of the watch which can be used in emails."""
        raise NotImplementedError


class EventUnion(Event):
    """Fireable conglomeration of multiple events

    Use this when you want to send a single mail to each person watching any of
    several events. For example, this sends only 1 mail to a given user, even
    if he was being notified of all 3 events:

        EventUnion(SomeEvent(), OtherEvent(), ThirdEvent()).fire()

    """
    # Calls some private methods on events, but this and Event are good
    # friends.

    def __init__(self, *events):
        """`events` -- the events of which to take the union"""
        super(EventUnion, self).__init__()
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

    def _users_watching(self, **kwargs):
        # Get a sorted iterable of user-watch pairs:
        users_and_watches = merge(*[e._users_watching(**kwargs)
                                    for e in self.events],
                                  key=lambda (user, watch): user.email.lower(),
                                  reverse=True)

        # Pick the best User out of each cluster of identical email addresses:
        return _unique_by_email(users_and_watches)


class InstanceEvent(Event):
    """Common case of watching a specific instance of a Model."""

    def __init__(self, instance, *args, **kwargs):
        super(InstanceEvent, self).__init__(*args, **kwargs)
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

    def _users_watching(self, **kwargs):
        """Return users watching this instance."""
        return self._users_watching_by_filter(object_id=self.instance.pk,
                                              **kwargs)
