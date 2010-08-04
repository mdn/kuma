import re

from django.contrib.auth.models import User

from sumo.models import TikiUser, ForumThread as TikiThread


ANONYMOUS_USER_NAME = 'AnonymousUser'


def get_fake_user():
    """Get a fake user. If one does not exist, create it."""
    try:
        return User.objects.get(username=ANONYMOUS_USER_NAME)
    except User.DoesNotExist:
        tiki_user = TikiUser.objects.create(
            login=ANONYMOUS_USER_NAME, password='md5$pass', hash='md5$hash',
            email='nobody@support.mozilla.com')
        return User.objects.create(
            id=tiki_user.userId, username=ANONYMOUS_USER_NAME,
            email='nobody@support.mozilla.com')


def get_django_user(obj, field_name='userName'):
    """Get the django user for this thread's username."""
    u = getattr(obj, field_name)
    try:
        user = User.objects.get(username=u)
    except User.DoesNotExist:
        # Assign a dummy user to this thread
        user = get_fake_user()

    return user


def fetch_threads(tiki_forum, num, offset=0):
    """Gets the next num threads for tiki_forum.forumId given offset."""
    # slice and dice
    start = offset
    end = offset + num

    return TikiThread.objects.filter(
        objectType='forum', object=tiki_forum.forumId, parentId=0).order_by(
        '-commentDate')[start:end]


def fetch_posts(tiki_thread, num, offset=0):
    """Gets the next num posts for tiki_thread.threadId given offset."""
    # slice and dice
    start = offset
    end = offset + num

    return TikiThread.objects.filter(
        objectType='forum', parentId=tiki_thread.threadId).order_by(
        '-commentDate')[start:end]


patterns_version = ('Firefox/(\S+)', 'Minefield/(\S+)')

# Store these to avoid recompiling on future calls of the get_firefox_version
compiled_patterns_version = []
for p in patterns_version:
    compiled_patterns_version.append(re.compile(p, re.IGNORECASE))


def get_firefox_version(user_agent):
    """
    Takes a user agent and returns the Firefox version.

    Ported from the JavaScript version in apps/media/questions.js
    """
    for p in compiled_patterns_version:
        m = p.search(user_agent)
        if m:
            return m.group(1)
    return ''


patterns_os = (
    ('Windows 3.11', 'Win16'),
    ('Windows 95', '(Windows 95)|(Win95)|(Windows_95)'),
    ('Windows 98', '(Windows 98)|(Win98)'),
    ('Windows 2000', '(Windows NT 5.0)|(Windows 2000)'),
    ('Windows XP', '(Windows NT 5.1)|(Windows XP)'),
    ('Windows Server 2003', '(Windows NT 5.2)'),
    ('Windows Vista', '(Windows NT 6.0)'),
    ('Windows 7', '(Windows NT 6.1)'),
    ('Windows NT 4.0', '(Windows NT 4.0)|(WinNT4.0)|(WinNT)|(Windows NT)'),
    ('Windows ME', 'Windows ME'),
    ('Windows', 'Windows'),
    ('OpenBSD', 'OpenBSD'),
    ('SunOS', 'SunOS'),
    ('Linux', '(Linux)|(X11)'),
    ('Mac OS X 10.4', '(Mac OS X 10.4)'),
    ('Mac OS X 10.5', '(Mac OS X 10.5)'),
    ('Mac OS X 10.6', '(Mac OS X 10.6)'),
    ('Mac OS', '(Mac_PowerPC)|(Macintosh)'),
    ('QNX', 'QNX'),
    ('BeOS', 'BeOS'),
    ('OS/2', 'OS/2'),
)

# Store these to avoid recompiling on future calls of the get_OS
compiled_patterns_os = []
for p in patterns_os:
    compiled_patterns_os.append((p[0], re.compile(p[1], re.IGNORECASE)))


def get_OS(user_agent):
    """
    Takes a user agent and returns the Operating System.

    Ported from the JavaScript version in apps/media/questions.js
    """
    for p in compiled_patterns_os:
        m = p[1].search(user_agent)
        if m:
            return p[0]
    return ''
