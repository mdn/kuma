# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from json import loads

from django.core.exceptions import ObjectDoesNotExist
from django.db import models, migrations


def move_to_user(apps, schema_editor):
    User = apps.get_model('users', 'User')

    unknowns = []
    users = User.objects.all().select_related('userprofile')
    count = users.count()
    if count:
        print('Porting %d user profiles' % count)

    for i, user in enumerate(users.iterator()):
        if i % 10000 == 0:
            print('%d/%d done' % (i, count))

        try:
            profile = user.userprofile_set.all().first()
        except ObjectDoesNotExist:
            continue

        if profile:
            user.bio = profile.bio
            user.content_flagging_email = profile.content_flagging_email
            user.fullname = profile.fullname
            user.homepage = profile.homepage
            user.irc_nickname = profile.irc_nickname
            user.locale = profile.locale or 'en-US'
            user.location = profile.location
            user.organization = profile.organization
            user.timezone = profile.timezone or 'US/Pacific'
            user.title = profile.title
            user.tags = profile.tags

            if profile.misc:
                websites = loads(profile.misc).get('websites', {})
                for name, url in websites.iteritems():
                    # make sure the stuff in the websites blob
                    # matches the field names we expect
                    try:
                        field_name = '%s_url' % name
                        user._meta.get_field(field_name)
                    except models.FieldDoesNotExist:
                        print('Tried porting profile %s and field %s' %
                              (profile.id, name))
                        raise
                    else:
                        setattr(user, field_name, url)
            user.save()
        else:
            unknowns.append(user.id)

    if unknowns:
        print('Found users whose profile could not be found: %s' % unknowns)


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_auto_20150722_1242'),
    ]

    operations = [
        migrations.RunPython(move_to_user),
    ]
