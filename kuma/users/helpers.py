from django.conf import settings
from django.contrib import admin

from jinja2 import escape, Markup, contextfunction
from jingo import register

from allauth.account.utils import user_display
from allauth.socialaccount import providers
from honeypot.templatetags.honeypot import render_honeypot_field
from tower import ugettext as _

from kuma.core.urlresolvers import reverse
from kuma.core.helpers import datetimeformat

from .jobs import UserGravatarURLJob


@register.function
def gravatar_url(user, secure=True, size=220, rating='pg',
                 default=settings.DEFAULT_AVATAR):
    job = UserGravatarURLJob()
    return job.get(user.email, secure=secure, size=size,
                   rating=rating, default=default)


@register.function
@contextfunction
def ban_link(context, ban_user, banner_user):
    """Returns a link to ban a user"""
    link = ''
    if ban_user.id != banner_user.id and banner_user.has_perm('users.add_userban'):
        if ban_user.profile.is_banned:
            active_ban = ban_user.profile.active_ban()
            url = reverse('admin:users_userban_change', args=(active_ban.id,))
            title = _('Banned on {ban_date} by {ban_admin}.').format(ban_date=datetimeformat(context, active_ban.date, format='date', output='json'), ban_admin=active_ban.by)
            link = '<a href="%s" class="button ban-link" title="%s">%s<i aria-hidden="true" class="icon-ban"></i></a>' % (url, title, _('Banned'))
        else:
            url = '%s?user=%s&by=%s' % (reverse('admin:users_userban_add'), ban_user.id, banner_user.id)
            link = '<a href="%s" class="button negative ban-link">%s<i aria-hidden="true" class="icon-ban"></i></a>' % (url, _('Ban User'))
    return Markup(link)


@register.function
def admin_link(user):
    """Returns a link to admin a user"""
    url = reverse('admin:users_user_change', args=(user.id,),
                  current_app=admin.site.name)
    link = ('<a href="%s" class="button neutral">%s'
            '<i aria-hidden="true" class="icon-wrench"></i></a>' %
            (url, _('Admin')))
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
        next = request.GET.get('next')
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


@register.inclusion_tag('honeypot/honeypot_field.html')
def honeypot_field(field_name=None):
    return render_honeypot_field(field_name)


register.function(user_display)
