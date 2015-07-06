import functools
import hashlib
import logging
import os
import random
import tempfile
import time
from itertools import islice

import lockfile
from celery import chain, chord
from polib import pofile

from django.conf import settings
from django.core.paginator import EmptyPage, InvalidPage, Paginator
from django.shortcuts import _get_queryset
from django.utils.encoding import force_unicode
from django.utils.http import urlencode

from taggit.utils import split_strip

from .cache import memcache
from .jobs import IPBanJob


log = logging.getLogger('kuma.core.utils')


def paginate(request, queryset, per_page=20):
    """Get a Paginator, abstracting some common paging actions."""
    paginator = Paginator(queryset, per_page)

    # Get the page from the request, make sure it's an int.
    try:
        page = int(request.GET.get('page', 1))
    except ValueError:
        page = 1

    # Get a page of results, or the first page if there's a problem.
    try:
        paginated = paginator.page(page)
    except (EmptyPage, InvalidPage):
        paginated = paginator.page(1)

    base = request.build_absolute_uri(request.path)

    items = [(k, v) for k in request.GET if k != 'page'
             for v in request.GET.getlist(k) if v]

    qsa = urlencode(items)

    paginated.url = u'%s?%s' % (base, qsa)
    return paginated


def smart_int(string, fallback=0):
    """Convert a string to int, with fallback for invalid strings or types."""
    try:
        return int(float(string))
    except (ValueError, TypeError):
        return fallback


def strings_are_translated(strings, locale):
    # http://stackoverflow.com/a/24339946/571420
    pofile_path = os.path.join(settings.ROOT, 'locale', locale, 'LC_MESSAGES',
                               'messages.po')
    try:
        po = pofile(pofile_path)
    except IOError:  # in case the file doesn't exist or couldn't be parsed
        return False
    all_strings_translated = True
    for string in strings:
        if not any(e for e in po if e.msgid == string and
                   (e.translated() and 'fuzzy' not in e.flags)
                   and not e.obsolete):
            all_strings_translated = False
    return all_strings_translated


def file_lock(prefix):
    """
    Decorator that only allows one instance of the same command to run
    at a time.
    """
    def decorator(f):
        @functools.wraps(f)
        def wrapper(self, *args, **kwargs):
            name = '_'.join((prefix, f.__name__) + args)
            file = os.path.join(tempfile.gettempdir(), name)
            lock = lockfile.FileLock(file)
            try:
                # Try to acquire the lock without blocking.
                lock.acquire(0)
            except lockfile.LockError:
                log.warning('Aborting %s; lock acquisition failed.' % name)
                return 0
            else:
                # We have the lock, call the function.
                try:
                    return f(self, *args, **kwargs)
                finally:
                    lock.release()
        return wrapper
    return decorator


def generate_filename_and_delete_previous(ffile, name, before_delete=None):
    """Generate a new filename for a file upload field; delete the previously
    uploaded file."""

    new_filename = ffile.field.generate_filename(ffile.instance, name)

    try:
        # HACK: Speculatively re-fetching the original object makes me feel
        # wasteful and dirty. But, I can't think of another way to get
        # to the original field's value. Should be cached, though.
        # see also - http://code.djangoproject.com/ticket/11663#comment:10
        orig_instance = ffile.instance.__class__.objects.get(
            id=ffile.instance.id
        )
        orig_field_file = getattr(orig_instance, ffile.field.name)
        orig_filename = orig_field_file.name

        if orig_filename and new_filename != orig_filename:
            if before_delete:
                before_delete(orig_field_file)
            orig_field_file.delete()
    except ffile.instance.__class__.DoesNotExist:
        pass

    return new_filename


class MemcacheLockException(Exception):
    pass


class MemcacheLock(object):
    def __init__(self, key, attempts=1, expires=60 * 60 * 3):
        self.key = 'lock_%s' % key
        self.attempts = attempts
        self.expires = expires
        self.cache = memcache

    def locked(self):
        return bool(self.cache.get(self.key))

    def acquire(self):
        for i in xrange(0, self.attempts):
            stored = self.cache.add(self.key, 1, self.expires)
            if stored:
                return True
            if i != self.attempts - 1:
                sleep_time = (((i + 1) * random.random()) + 2 ** i) / 2.5
                logging.debug('Sleeping for %s while trying to acquire key %s',
                              sleep_time, self.key)
                time.sleep(sleep_time)
        raise MemcacheLockException('Could not acquire lock for %s' % self.key)

    def release(self):
        self.cache.delete(self.key)


def get_object_or_none(klass, *args, **kwargs):
    """
    A tool like Django's get_object_or_404 but returns None in case
    of a DoesNotExist exception.
    """
    queryset = _get_queryset(klass)
    try:
        return queryset.get(*args, **kwargs)
    except queryset.model.DoesNotExist:
        return None


def parse_tags(tagstring, sorted=True):
    """
    Parses tag input, with multiple word input being activated and
    delineated by commas and double quotes. Quotes take precedence, so
    they may contain commas.

    Returns a sorted list of unique tag names, unless sorted=False.

    Ported from Jonathan Buchanan's `django-tagging
    <http://django-tagging.googlecode.com/>`_
    """
    if not tagstring:
        return []

    tagstring = force_unicode(tagstring)

    # Special case - if there are no commas or double quotes in the
    # input, we don't *do* a recall... I mean, we know we only need to
    # split on spaces.
    if u',' not in tagstring and u'"' not in tagstring:
        words = list(split_strip(tagstring, u' '))
        if sorted:
            words.sort()
        return words

    words = []
    buffer = []
    # Defer splitting of non-quoted sections until we know if there are
    # any unquoted commas.
    to_be_split = []
    saw_loose_comma = False
    open_quote = False
    i = iter(tagstring)
    try:
        while True:
            c = i.next()
            if c == u'"':
                if buffer:
                    to_be_split.append(u''.join(buffer))
                    buffer = []
                # Find the matching quote
                open_quote = True
                c = i.next()
                while c != u'"':
                    buffer.append(c)
                    c = i.next()
                if buffer:
                    word = u''.join(buffer).strip()
                    if word:
                        words.append(word)
                    buffer = []
                open_quote = False
            else:
                if not saw_loose_comma and c == u',':
                    saw_loose_comma = True
                buffer.append(c)
    except StopIteration:
        # If we were parsing an open quote which was never closed treat
        # the buffer as unquoted.
        if buffer:
            if open_quote and u',' in buffer:
                saw_loose_comma = True
            to_be_split.append(u''.join(buffer))
    if to_be_split:
        if saw_loose_comma:
            delimiter = u','
        else:
            delimiter = u' '
        for chunk in to_be_split:
            words.extend(split_strip(chunk, delimiter))
    words = list(words)
    if sorted:
        words.sort()
    return words


def chunked(iterable, n):
    """Return chunks of n length of iterable.

    If ``len(iterable) % n != 0``, then the last chunk will have
    length less than n.

    Example:

    >>> chunked([1, 2, 3, 4, 5], 2)
    [(1, 2), (3, 4), (5,)]

    :arg iterable: the iterable
    :arg n: the chunk length

    :returns: generator of chunks from the iterable
    """
    iterable = iter(iterable)
    while 1:
        t = tuple(islice(iterable, n))
        if t:
            yield t
        else:
            return


def chord_flow(pre_task, tasks, post_task):

    if settings.CELERY_ALWAYS_EAGER:
        # Eager mode and chords don't get along. So we serialize
        # the tasks as a workaround.
        tasks.insert(0, pre_task)
        tasks.append(post_task)
        return chain(*tasks)
    else:
        return chain(pre_task, chord(header=tasks, body=post_task))


def limit_banned_ip_to_0(group, request):
    ip = request.META.get('REMOTE_ADDR', '10.0.0.1')
    return IPBanJob().get(ip)


def get_unique(content_type, object_pk, name=None, request=None,
               ip=None, user_agent=None, user=None):
    """Extract a set of unique identifiers from the request.

    This set will be made up of one of the following combinations, depending
    on what's available:

    * user, None, None, unique_MD5_hash
    * None, ip, user_agent, unique_MD5_hash
    """
    if request:
        if request.user.is_authenticated():
            user = request.user
            ip = user_agent = None
        else:
            user = None
            ip = request.META.get('REMOTE_ADDR', '')
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:255]

    # HACK: Build a hash of the fields that should be unique, let MySQL
    # chew on that for a unique index. Note that any changes to this algo
    # will create all new unique hashes that don't match any existing ones.
    hash_text = "\n".join(unicode(x).encode('utf-8') for x in (
        content_type.pk, object_pk, name or '', ip, user_agent,
        (user and user.pk or 'None')
    ))
    unique_hash = hashlib.md5(hash_text).hexdigest()

    return (user, ip, user_agent, unique_hash)
