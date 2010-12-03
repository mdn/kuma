from jingo import register


@register.function
def profile_url(user):
    """Return a URL to the user's profile."""
    # TODO: revisit this when we have a users app
    return '/tiki-user_information.php?locale=en-US&userId=%s' % user.id


@register.function
def profile_avatar(user):
    """Return a URL to the user's avatar."""
    # TODO: revisit this when we have a users app
    return '/tiki-show_user_avatar.php?user=%s' % user.username
