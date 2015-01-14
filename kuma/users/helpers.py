import urllib
import hashlib

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from jinja2 import escape, Markup, contextfunction
from jingo import register

from allauth.account.utils import user_display
from allauth.socialaccount import providers
from tower import ugettext as _

from sumo.urlresolvers import reverse

from devmo.helpers import datetimeformat

DEFAULT_AVATAR = getattr(settings, 'DEFAULT_AVATAR',
                         settings.MEDIA_URL + 'img/avatar-default.png')


@register.function
def gravatar_url(user, secure=True, size=220, rating='pg',
                 default=DEFAULT_AVATAR):
    """Produce a gravatar image URL from email address."""
    base_url = (secure and 'https://secure.gravatar.com' or
                'http://www.gravatar.com')
    email_hash = hashlib.md5(user.email.lower().encode('utf8'))
    params = urllib.urlencode({'s': size, 'd': default, 'r': rating})
    return '%(base_url)s/avatar/%(hash)s?%(params)s' % {
        'base_url': base_url,
        'hash': email_hash.hexdigest(),
        'params': params,
    }


@register.function
@contextfunction
def ban_link(context, ban_user, banner_user):
    """Returns a link to ban a user"""
    link = ''
    if ban_user.id != banner_user.id and banner_user.has_perm('users.add_userban'):
        if ban_user.get_profile().is_banned:
            active_ban = ban_user.get_profile().active_ban()
            # TODO: link to the active ban
            link = '<a class="button inactive ban-link" title="%s %s %s %s">%s</a>' % (_('Banned'), datetimeformat(context, active_ban.date, format='date', output='json'), _('by'), active_ban.by, _('Banned'))
        else:
            url = '%s?user=%s&by=%s' % (reverse('admin:users_userban_add'), ban_user.id, banner_user.id)
            link = '<a href="%s" class="button negative ban-link">%s</a>' % (url, _('Ban User'))
    return Markup(link)


@register.filter
def public_email(email):
    """Email address -> publicly displayable email."""
    return Markup('<span class="email">%s</span>' % unicode_to_html(email))


def unicode_to_html(text):
    """Turns all unicode into html entities, e.g. &#69; -> E."""
    return ''.join([u'&#%s;' % ord(i) for i in text])


@register.function
def user_list(users):
    """Turn a list of users into a list of links to their profiles."""
    link = u'<a href="%s">%s</a>'
    list = u', '.join([link % (escape(u.get_absolute_url()), escape(u.username)) for
                       u in users])
    return Markup(list)


@register.function
@contextfunction
def provider_login_url(context, provider_id, **params):
    """
    {{ provider_login_url("github", next="/some/url") }}
    {{ provider_login_url("persona", next="/some/other/url") }}
    """
    request = context['request']
    provider = providers.registry.by_id(provider_id)
    if 'next' not in params:
        next = request.REQUEST.get('next')
        if next:
            params['next'] = next
    else:
        if not params['next']:
            del params['next']
    return Markup(provider.get_login_url(request, **params))


@register.function
@contextfunction
def providers_media_js(context):
    """
    {{ providers_media_js() }}
    """
    request = context['request']
    return Markup(u'\n'.join([p.media_js(request)
                             for p in providers.registry.get_list()]))


@register.function
def social_accounts(user):
    """
    {% set accounts = social_accounts(user) %}

    Then:
        {{ accounts.twitter }} -- a list of connected Twitter accounts
        {{ accounts.twitter.0 }} -- the first Twitter account
        {% if accounts %} -- if there is at least one social account
    """
    accounts = {}
    if not user.is_authenticated():
        return accounts
    for account in user.socialaccount_set.all().iterator():
        providers = accounts.setdefault(account.provider, [])
        providers.append(account)
    return accounts


register.function(user_display)
