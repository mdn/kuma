from datetime import datetime
from optparse import make_option
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from PIL import Image

from sumo.models import TikiUser
from sumo.utils import chunked
from upload.tasks import _scale_dimensions
from users.models import User, Profile


AVATAR_ROOT = os.path.join(settings.MEDIA_ROOT, settings.USER_AVATAR_PATH)
AVATAR_PATH = os.path.join(AVATAR_ROOT, 'avatar-%s.png')


class Command(BaseCommand):  #pragma: no cover
    help = 'Migrate user avatars out of the database.'
    option_list = BaseCommand.option_list + (
        make_option('--start',
            action='store',
            type=int,
            dest='start',
            default=0,
            help='Where to start.'),
        make_option('--end',
            action='store',
            type=int,
            dest='end',
            default=None,
            help='Where to end.'),
        )

    def handle(self, *args, **options):
        print 'Writing avatars to %s' % AVATAR_PATH
        start = options['start']
        end = options['end']
        print 'Starting at %s, going until %s' % (start, end)

        # Grab all the known Tiki users.
        users = TikiUser.objects.all().values_list('pk',
                                                   flat=True)[start:end]

        # In case it doesn't exist.
        if not os.path.exists(AVATAR_ROOT):
            os.makedirs(AVATAR_ROOT)

        total = 0

        for chunk in chunked(users, 1000):
            total += len(chunk)
            print 'Processing %s users (%s total)' % (len(chunk),
                                                      total + start)

            for pk in chunk:

                # Load or create a Django user.
                tu = TikiUser.objects.get(pk=pk)
                try:
                    du = User.objects.get(username=tu.login)
                except User.DoesNotExist:
                    du = User(username=tu.login,
                              email=tu.email,
                              password=tu.hash,
                              is_active=True,
                              date_joined=datetime.fromtimestamp(
                                tu.registrationDate))
                    du.save()

                # Load or (usually) create a profile.
                try:
                    profile = du.get_profile()
                    if profile.avatar:  # Already has an avatar, skip it.
                        continue
                except Profile.DoesNotExist:
                    profile = Profile.objects.create(user=du)

                # Set livechat_id
                profile.livechat_id = tu.livechat_id

                if tu.avatarFileType and tu.avatarFileType.startswith('image'):

                    # What format is it currently in?
                    format = 'png'
                    if tu.avatarFileType == 'image/gif':
                        format = 'gif'
                    elif tu.avatarFileType == 'image/jpeg':
                        format = 'jpg'

                    # Write the avatar data to a file.
                    fname = '/tmp/avatar-%s.%s' % (pk, format)
                    with open(fname, 'wb') as fp:
                        fp.write(tu.avatarData)

                    try:
                        # Maybe resize, convert to PNG.
                        image = Image.open(fname)
                        # 48x48 is the size of all the avatars we've created.
                        size = _scale_dimensions(*image.size, longest_side=48)
                        avatar = image.resize(size, resample=1)
                        avatar.save(AVATAR_PATH % du.pk)

                        profile.avatar = AVATAR_PATH % du.pk
                    except IOError:
                        pass  # Couldn't read or write the image.

                    # Clean up.
                    os.unlink(fname)

                profile.save()
