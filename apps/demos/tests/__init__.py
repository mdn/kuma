# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime

from django.contrib.auth.models import User

from demos.models import Submission


def make_users():
    user = User.objects.create_user(
        'tester', 'tester@tester.com', 'tester')
    user.save()

    admin_user = User.objects.create_superuser(
        'admin_tester', 'admin_tester@tester.com', 'admint_tester')
    admin_user.save()

    other_user = User.objects.create_user(
        'visitor', 'visitor@visitor.com', 'visitor')
    other_user.save()

    return (user, admin_user, other_user)


def build_submission(creator):
    now = str(datetime.datetime.now())

    s = Submission(title='Hello world' + now, slug='hello-world' + now,
        description='This is a hello world demo', hidden=False,
        creator=creator)
    s.save()

    return s


def build_hidden_submission(creator, slug='hidden-world'):
    now = str(datetime.datetime.now())

    s = Submission(title='Hidden submission 1' + now, slug=slug + now,
        description='This is a hidden demo', hidden=True,
        creator=creator)
    s.save()

    return s
