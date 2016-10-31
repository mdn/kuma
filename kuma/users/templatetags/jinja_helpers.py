from allauth.account.utils import user_display
from allauth.socialaccount import providers
from allauth.socialaccount.templatetags.socialaccount import get_providers
from allauth.utils import get_request_param
from django.conf import settings
from django.contrib import admin
from django.utils.translation import ugettext
from django_jinja import library
from honeypot.templatetags.honeypot import render_honeypot_field
from jinja2 import Markup, contextfunction, escape

from kuma.core.templatetags.jinja_helpers import datetimeformat
from kuma.core.urlresolvers import reverse

from ..jobs import UserGravatarURLJob


@library.global_function
def gravatar_url(email, secure=True, size=220, rating='pg',
                 default=settings.DEFAULT_AVATAR):
    job = UserGravatarURLJob()
    return job.get(email, secure=secure, size=size,
                   rating=rating, default=default)


@library.global_function
@contextfunction
def ban_links(context, ban_user, banner_user):
    """Returns a link to ban a user"""
    links = ''
    if ban_user.id != banner_user.id and banner_user.has_perm('users.add_userban'):
        active_ban = ban_user.active_ban
        url_ban_cleanup = reverse('users.ban_user_and_cleanup',
                                  kwargs={'username': ban_user.username})
        if active_ban:
            url = reverse('admin:users_userban_change', args=(active_ban.id,))
            title = ugettext('Banned on %(ban_date)s by %(ban_admin)s.') % {
                'ban_date': datetimeformat(context, active_ban.date,
                                           format='date', output='json'),
                'ban_admin': active_ban.by,
            }
            link = ('<a id="ban_link" href="%s" class="button ban-link" title="%s">%s'
                    '<i aria-hidden="true" class="icon-ban"></i></a>'
                    % (url, title, ugettext('Banned')))
            link_cleanup = ('<a id="cleanup_link" href="%s" class="button negative ban-link">%s'
                            '<i aria-hidden="true" class="icon-ban"></i></a>'
                            % (url_ban_cleanup, ugettext('Clean Up Revisions')))
        else:
            url = reverse('users.ban_user', kwargs={'username': ban_user.username})
            link = ('<a id="ban_link" href="%s" class="button negative ban-link">%s'
                    '<i aria-hidden="true" class="icon-ban"></i></a>'
                    % (url, ugettext('Ban User')))
            link_cleanup = ('<a id="cleanup_link" href="%s" class="button negative ban-link">%s'
                            '<i aria-hidden="true" class="icon-ban"></i></a>'
                            % (url_ban_cleanup, ugettext('Ban User & Clean Up')))
        links = link_cleanup + ' ' + link
    return Markup(links)


@library.global_function
def admin_link(user):
    """Returns a link to admin a user"""
    url = reverse('admin:users_user_change', args=(user.id,),
                  current_app=admin.site.name)
    link = ('<a href="%s" class="button neutral">%s'
            '<i aria-hidden="true" class="icon-wrench"></i></a>' %
            (url, ugettext('Admin')))
    return Markup(link)


@library.filter
def public_email(email):
    """Email address -> publicly displayable email."""
    return Markup('<span class="email">%s</span>' % unicode_to_html(email))


def unicode_to_html(text):
    """Turns all unicode into html entities, e.g. &#69; -> E."""
    return ''.join([u'&#%s;' % ord(i) for i in text])


@library.global_function
def user_list(users):
    """Turn a list of users into a list of links to their profiles."""
    link = u'<a href="%s">%s</a>'
    list = u', '.join([link % (escape(u.get_absolute_url()), escape(u.username)) for
                       u in users])
    return Markup(list)


# Returns a string representation of a user
library.global_function(user_display)

# Returns a list of social authentication providers.
library.global_function(get_providers)


@library.global_function
@contextfunction
def provider_login_url(context, provider_id, **params):
    """
    {{ provider_login_url("github", next="/some/url") }}
    """
    request = context['request']
    provider = providers.registry.by_id(provider_id)
    auth_params = params.get('auth_params', None)
    scope = params.get('scope', None)
    process = params.get('process', None)
    if scope is '':
        del params['scope']
    if auth_params is '':
        del params['auth_params']
    if 'next' not in params:
        next = get_request_param(request, 'next')
        if next:
            params['next'] = next
        elif process == 'redirect':
            params['next'] = request.get_full_path()
    else:
        if not params['next']:
            del params['next']
    # get the login url and append params as url parameters
    return Markup(provider.get_login_url(request, **params))


@library.global_function
@contextfunction
def providers_media_js(context):
    """
    {{ providers_media_js() }}
    """
    request = context['request']
    return Markup(u'\n'.join([p.media_js(request)
                             for p in providers.registry.get_list()]))


@library.global_function
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


@library.global_function
@library.render_with('honeypot/honeypot_field.html')
def honeypot_field(field_name=None):
    return render_honeypot_field(field_name)
