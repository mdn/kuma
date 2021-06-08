import logging
import os
from smtplib import SMTPConnectError, SMTPServerDisconnected
from urllib.parse import parse_qsl, ParseResult, urlparse, urlsplit, urlunsplit

import requests
from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
from django.http import QueryDict
from django.utils.cache import patch_cache_control
from django.utils.encoding import smart_bytes
from django.utils.http import urlencode
from polib import pofile
from pyquery import PyQuery as pq
from redo import retrying
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


log = logging.getLogger("kuma.core.utils")


def strings_are_translated(strings, locale):
    # http://stackoverflow.com/a/24339946/571420
    pofile_path = os.path.join(
        settings.ROOT, "locale", locale, "LC_MESSAGES", "django.po"
    )
    try:
        po = pofile(pofile_path)
    except IOError:  # in case the file doesn't exist or couldn't be parsed
        return False
    all_strings_translated = True
    for string in strings:
        if not any(
            e
            for e in po
            if e.msgid == string
            and (e.translated() and "fuzzy" not in e.flags)
            and not e.obsolete
        ):
            all_strings_translated = False
    return all_strings_translated


def urlparams(url_, fragment=None, query_dict=None, **query):
    """
    Add a fragment and/or query parameters to a URL.

    New query params will be appended to exising parameters, except duplicate
    names, which will be replaced.
    """
    url_ = urlparse(url_)
    fragment = fragment if fragment is not None else url_.fragment

    q = url_.query
    new_query_dict = (
        QueryDict(smart_bytes(q), mutable=True) if q else QueryDict("", mutable=True)
    )
    if query_dict:
        for k, l in query_dict.lists():
            new_query_dict[k] = None  # Replace, don't append.
            for v in l:
                new_query_dict.appendlist(k, v)

    for k, v in query.items():
        # Replace, don't append.
        if isinstance(v, list):
            new_query_dict.setlist(k, v)
        else:
            new_query_dict[k] = v

    query_string = urlencode(
        [(k, v) for k, l in new_query_dict.lists() for v in l if v is not None]
    )
    new = ParseResult(
        url_.scheme, url_.netloc, url_.path, url_.params, query_string, fragment
    )
    return new.geturl()


def add_shared_cache_control(response, **kwargs):
    """
    Adds a Cache-Control header for shared caches, like CDNs, to the
    provided response.

    Default settings (which can be overridden or extended):
    - max-age=0 - Don't use browser cache without asking if still valid
    - s-maxage=CACHE_CONTROL_DEFAULT_SHARED_MAX_AGE - Cache in the shared
      cache for the default perioid of time
    - public - Allow intermediate proxies to cache response
    """
    nocache = response.has_header("Cache-Control") and (
        "no-cache" in response["Cache-Control"]
        or "no-store" in response["Cache-Control"]
    )
    if nocache:
        return

    # Set the default values.
    cc_kwargs = {
        "public": True,
        "max_age": 0,
        "s_maxage": settings.CACHE_CONTROL_DEFAULT_SHARED_MAX_AGE,
    }
    # Override the default values and/or add new ones.
    cc_kwargs.update(kwargs)

    patch_cache_control(response, **cc_kwargs)


def order_params(original_url):
    """Standardize order of query parameters."""
    bits = urlsplit(original_url)
    qs = sorted(parse_qsl(bits.query, keep_blank_values=True))
    new_qs = urlencode(qs)
    new_url = urlunsplit((bits.scheme, bits.netloc, bits.path, new_qs, bits.fragment))
    return new_url


def requests_retry_session(
    retries=3,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 504),
):
    """Opinionated wrapper that creates a requests session with a
    HTTPAdapter that sets up a Retry policy that includes connection
    retries.

    If you do the more naive retry by simply setting a number. E.g.::

        adapter = HTTPAdapter(max_retries=3)

    then it will raise immediately on any connection errors.
    Retrying on connection errors guards better on unpredictable networks.
    From http://docs.python-requests.org/en/master/api/?highlight=retries#requests.adapters.HTTPAdapter
    it says: "By default, Requests does not retry failed connections."

    The backoff_factor is documented here:
    https://urllib3.readthedocs.io/en/latest/reference/urllib3.util.html#urllib3.util.retry.Retry
    A default of retries=3 and backoff_factor=0.3 means it will sleep like::

        [0.3, 0.6, 1.2]
    """  # noqa
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def safer_pyquery(*args, **kwargs):
    """
    PyQuery is magically clumsy in how it handles its arguments. A more
    ideal and explicit constructor would be:

        >>> from pyquery import PyQuery as pq
        >>> parsed = pq(html=my_html_string)
        >>> parsed = pq(url=definitely_a_url_string)

    But instead, you're expected to use it like this:

        >>> from pyquery import PyQuery as pq
        >>> parsed = pq(my_html_string)
        >>> parsed = pq(definitely_a_url_string)

    ...and PyQuery attempts to be smart and look at that first argument
    and if it looks like a URL, it first calls `requests.get()` on it.

    This function is a thin wrapper on that constructor that prevents
    that dangerous code to ever get a chance.

    NOTE! As of May 10 2019, this risk exists the the latest release of
    PyQuery. Hopefully it will be fixed but it would a massively disruptive
    change and thus unlikely to happen any time soon.

    NOTE 2! Unlikely to be fixed by core pyquery team any time soon
    https://github.com/gawel/pyquery/issues/203
    """

    # This "if" statement is exactly what PyQuery's constructor does.
    # We'll run it ourselves once and if it matches, "ruin" it by
    # injecting that extra space.
    if (
        len(args) >= 1
        and isinstance(args[0], str)
        and args[0].split("://", 1)[0] in ("http", "https")
    ):
        args = (f" {args[0]}",) + args[1:]

    return pq(*args, **kwargs)


def send_mail_retrying(
    subject,
    message,
    from_email,
    recipient_list,
    fail_silently=False,
    auth_user=None,
    auth_password=None,
    connection=None,
    html_message=None,
    attachment=None,
    **kwargs,
):
    """Copied verbatim from django.core.mail.send_mail but with the override
    that we're using our EmailMultiAlternativesRetrying class instead.
    See its doc string for its full documentation.

    The only difference is that this function allows for setting your
    own custom 'retrying' keyword argument.
    """
    connection = connection or get_connection(
        username=auth_user,
        password=auth_password,
        fail_silently=fail_silently,
    )
    mail = EmailMultiAlternativesRetrying(
        subject, message, from_email, recipient_list, connection=connection
    )
    if html_message:
        mail.attach_alternative(html_message, "text/html")

    if attachment:
        mail.attach(attachment["name"], attachment["bytes"], attachment["mime"])

    return mail.send(**kwargs)


class EmailMultiAlternativesRetrying(EmailMultiAlternatives):
    """
    Thin wrapper on django.core.mail.EmailMultiAlternatives that adds
    a retrying functionality. By default, the only override is that
    we're very explicit about the of exceptions we treat as retry'able.
    The list of exceptions we use to trigger a retry are:

        * smtplib.SMTPConnectError
        * smtplib.SMTPServerDisconnected

    Only list exceptions that have been known to happen and are safe.
    """

    def send(self, *args, retry_options=None, **kwargs):
        # See https://github.com/mozilla-releng/redo
        # for a list of the default options to the redo.retry function
        # which the redo.retrying context manager wraps.
        retry_options = retry_options or {
            "retry_exceptions": (SMTPConnectError, SMTPServerDisconnected),
            # The default in redo is 60 seconds. Let's tone that down.
            "sleeptime": 3,
            "attempts": 10,
        }

        parent_method = super(EmailMultiAlternativesRetrying, self).send
        with retrying(parent_method, **retry_options) as method:
            return method(*args, **kwargs)
