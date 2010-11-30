from django.conf import settings
from django.contrib.auth.models import User
from django.db import models

from timezones.fields import TimeZoneField
from tower import ugettext_lazy as _lazy

from sumo.models import ModelBase
from countries import COUNTRIES


# TODO: detect timezone automatically from client side, see
# http://rocketscience.itteco.org/2010/03/13/automatic-users-timezone-determination-with-javascript-and-django-timezones/


class Profile(ModelBase):
    """Profile model for django users, get it with user.get_profile()."""

    user = models.OneToOneField(User, primary_key=True,
                                verbose_name=_lazy('User'))
    name = models.CharField(max_length=255, verbose_name=_lazy('Full Name'))
    public_email = models.BooleanField(  # show/hide email
        default=False, verbose_name=_lazy('Make my email public'))
    avatar = models.ImageField(upload_to=settings.USER_AVATAR_PATH, null=True,
                               blank=True, verbose_name=_lazy('Avatar'),
                               max_length=settings.MAX_FILEPATH_LENGTH)
    bio = models.TextField(null=True, blank=True,
                           verbose_name=_lazy('Biography'))
    # verify_exists=True by default for URLs
    website = models.URLField(max_length=255, null=True, blank=True,
                              verbose_name=_lazy('Website'))
    twitter = models.URLField(max_length=255, null=True, blank=True,
                              verbose_name=_lazy('Twitter URL'))
    facebook = models.URLField(max_length=255, null=True, blank=True,
                               verbose_name=_lazy('Facebook URL'))
    irc_handle = models.CharField(max_length=255, null=True, blank=True,
                                  verbose_name=_lazy('IRC Nickname'))
    timezone = TimeZoneField(null=True, blank=True,
                             verbose_name=_lazy('Timezone'))
    country = models.CharField(max_length=2, choices=COUNTRIES, null=True,
                               blank=True, verbose_name=_lazy('Country'))
    # No city validation
    city = models.CharField(max_length=255, null=True, blank=True,
                            verbose_name=_lazy('City'))
    livechat_id = models.CharField(default=None, null=True, blank=True,
                                   max_length=255,
                                   verbose_name=_lazy('Livechat ID'))
