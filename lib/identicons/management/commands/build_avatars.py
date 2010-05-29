"""
build_avatars: a management command to create avatars for users who don't
have them.

Goes through and grabs all users without avatars, then creates an image by
taking the MD5 of the user's email address and passing it to
render_identicon. Then we need to save the image to get PIL to output it
in PNG format instead of raw RGB. Finally we read back the file and save it
into Tiki's database, which is what Tiki requires for avatars.

This needs to get run periodically to create avatars for newly registered
users.

TODO:
* Once we're handling user registration in Kitsune, we will pull avatars
  out of the database and serve them as files, the way Tim intended.
* We'll also eventually use a celery task to generate the avatar at
  registration.
"""

import os
import hashlib

from django.core.management.base import BaseCommand
from django.utils.encoding import DjangoUnicodeDecodeError

from identicons import render_identicon

from sumo.models import TikiUser


IMAGE_SIZE = 16


class Command(BaseCommand):  #pragma: no cover
    help = ("Builds avatars for users with no or bad avatar data.")

    requires_model_validation = False

    def handle(self, **options):
        print 'Fetching users...'
        users = TikiUser.objects.filter(avatarData__isnull=True)

        for u in users:
            print 'Hashing %s' % u.login
            # Ugh, this part gets ugly.
            h = hashlib.md5(u.email).hexdigest()
            i = int(h, 16)
            iname = '/tmp/%s.png' % h

            img = render_identicon(i, IMAGE_SIZE)
            img.save(iname)

            with open(iname) as fp:
                idata = fp.read()
                u.avatarData = idata
                u.avatarFileType = 'image/png'
                u.avatarSize = len(idata)

            try:
                u.save()
            except DjangoUnicodeDecodeError:
                # It will always throw these.
                pass

            del img
            os.unlink(iname)
