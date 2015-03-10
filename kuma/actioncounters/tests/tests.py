from django.conf import settings

from django.core.exceptions import MultipleObjectsReturned

from django.contrib.auth.models import AnonymousUser

from django.http import HttpRequest
from django.test import TestCase
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User

from nose.tools import eq_, ok_
from nose.plugins.attrib import attr

from ..utils import get_unique
from ..models import ActionCounterUnique
from .models import TestModel


class ActionCountersTest(TestCase):

    def setUp(self):
        super(ActionCountersTest, self).setUp()
        self.user1 = User.objects.create_user(
            'tester1', 'tester2@tester.com', 'tester1')
        self.user2 = User.objects.create_user(
            'tester2', 'tester2@tester.com', 'tester2')

        self.obj_1 = TestModel(title="alpha")
        self.obj_1.save()

    def mk_request(self, user=None, ip='192.168.123.123', user_agent='FakeBrowser 1.0'):
        request = HttpRequest()
        request.user = user and user or AnonymousUser()
        request.method = 'GET'
        request.META['REMOTE_ADDR'] = ip
        request.META['HTTP_USER_AGENT'] = user_agent
        return request

    @attr('bug694544')
    def test_bug694544(self):
        """Bug 694544: unicode character in request details should not break"""
        try:
            action_name = "likes"
            obj_1 = self.obj_1
            obj_1_ct = ContentType.objects.get_for_model(obj_1)

            request = self.mk_request(user_agent="Some\xef\xbf\xbdbrowser")
            user, ip, user_agent, unique_hash = get_unique(obj_1_ct, obj_1.pk,
                                                           action_name, request)
        except UnicodeDecodeError:
            ok_(False, "UnicodeDecodeError should not be thrown")

    @attr('bad_multiple')
    def test_bad_multiple_counters(self):
        """
        Force multiple counters, possibly result of race condition,
        ensure graceful handling
        """
        action_name = "likes"
        obj_1 = self.obj_1
        obj_1_ct = ContentType.objects.get_for_model(obj_1)

        request = self.mk_request()
        user, ip, user_agent, unique_hash = get_unique(obj_1_ct, obj_1.pk,
                                                       action_name, request)

        # Create an initial counter record directly.
        u1 = ActionCounterUnique(content_type=obj_1_ct, object_pk=obj_1.pk,
                name=action_name, total=1, ip=ip, user_agent=user_agent,
                user=user)
        u1.save()

        # Adding a duplicate counter should be prevented at the model level.
        try:
            u2 = ActionCounterUnique(content_type=obj_1_ct, object_pk=obj_1.pk,
                    name=action_name, total=1, ip=ip, user_agent=user_agent,
                    user=user)
            u2.save()
            ok_(False, "This should have triggered an IntegrityError")
        except:
            pass

        # Try get_unique_for_request, which should turn up the single unique
        # record created earlier.
        try:
            (u, created) = ActionCounterUnique.objects.get_unique_for_request(obj_1,
                               action_name, request)
            eq_(False, created)
        except MultipleObjectsReturned, e:
            ok_(False, "MultipleObjectsReturned should not be raised")

    def test_basic_action_increment(self):
        """Action attempted with several different kinds of unique identifiers"""

        obj_1 = self.obj_1

        # set up request for anonymous user #1
        request = self.mk_request()

        # anonymous user #1 likes user2
        obj_1.likes.increment(request)
        eq_(1, obj_1.likes.total)

        # anonymous user #1 likes user2, again
        obj_1.likes.increment(request)
        eq_(1, obj_1.likes.total)

        # set up request for anonymous user #2
        request = self.mk_request(ip='192.168.123.1')

        # anonymous user #2 likes user2
        obj_1.likes.increment(request)
        eq_(2, obj_1.likes.total)

        # anonymous user #2 likes user2, again
        obj_1.likes.increment(request)
        eq_(2, obj_1.likes.total)

        # set up request for authenticated user1
        request = self.mk_request(user=self.user1)

        # authenticated user1 likes user2
        obj_1.likes.increment(request)
        eq_(3, obj_1.likes.total)

        # authenticated user1 likes user2, again
        obj_1.likes.increment(request)
        eq_(3, obj_1.likes.total)

        # authenticated user1 likes user2, again, from another IP
        request.META['REMOTE_ADDR'] = '192.168.123.50'
        obj_1.likes.increment(request)
        eq_(3, obj_1.likes.total)

        # set up request for user agent Mozilla 1.0
        request = self.mk_request(ip='192.168.123.50',
                                  user_agent='Mozilla 1.0')
        obj_1.likes.increment(request)
        eq_(4, obj_1.likes.total)

        # set up request for user agent Safari 1.0
        request = self.mk_request(ip='192.168.123.50', user_agent='Safari 1.0')
        obj_1.likes.increment(request)
        eq_(5, obj_1.likes.total)

    def test_action_with_max(self):
        """Action with a max_total_per_unique greater than 1"""
        obj_1 = self.obj_1
        MAX = obj_1.views.field.max_total_per_unique

        request = self.mk_request(ip='192.168.123.123')
        for x in range(1, MAX + 1):
            obj_1.views.increment(request)
            eq_(x, obj_1.views.total)

        obj_1.views.increment(request)
        eq_(MAX, obj_1.views.total)

        obj_1.views.increment(request)
        eq_(MAX, obj_1.views.total)

    def test_action_with_min(self):
        """Action with a min_total_per_unique greater than 1"""
        obj_1 = self.obj_1
        MIN = obj_1.frobs.field.min_total_per_unique

        request = self.mk_request(ip='192.168.123.123')
        for x in range(1, (0-MIN)+1):
            obj_1.frobs.decrement(request)
            eq_(0-x, obj_1.frobs.total)

        obj_1.frobs.decrement(request)
        eq_(MIN, obj_1.frobs.total)

        obj_1.frobs.decrement(request)
        eq_(MIN, obj_1.frobs.total)

    def test_action_count_per_unique(self):
        """Exercise action counts per unique and ensure overall total works"""
        obj_1 = self.obj_1

        MAX = obj_1.boogs.field.max_total_per_unique
        MIN = obj_1.boogs.field.min_total_per_unique

        UNIQUES = (
            dict(user=self.user1),
            dict(user=self.user2),
            dict(ip='192.168.123.123'),
            dict(ip='192.168.123.150', user_agent="Safari 1.0"),
            dict(ip='192.168.123.150', user_agent="Mozilla 1.0"),
            dict(ip='192.168.123.160'),
        )

        for unique in UNIQUES:
            request = self.mk_request(**unique)

            for x in range(1, MAX+1):
                obj_1.boogs.increment(request)
                eq_(x, obj_1.boogs.get_total_for_request(request))

            obj_1.boogs.increment(request)
            obj_1.boogs.increment(request)
            eq_(MAX, obj_1.boogs.get_total_for_request(request))

        eq_(MAX * len(UNIQUES), obj_1.boogs.total)

        # Undo all the increments before going below zero
        for unique in UNIQUES:
            request = self.mk_request(**unique)
            for x in range(1, MAX + 1):
                obj_1.boogs.decrement(request)

        for unique in UNIQUES:
            request = self.mk_request(**unique)

            for x in range(1, (0 - MIN) + 1):
                obj_1.boogs.decrement(request)
                eq_(0 - x, obj_1.boogs.get_total_for_request(request))

            obj_1.boogs.decrement(request)
            obj_1.boogs.decrement(request)
            eq_(MIN, obj_1.boogs.get_total_for_request(request))

        eq_(MIN * len(UNIQUES), obj_1.boogs.total)

    def test_count_starts_at_zero(self):
        """
        Make sure initial count is zero.

        Sounds dumb, but it was a bug at one point.
        """
        request = self.mk_request()
        eq_(0, self.obj_1.likes.get_total_for_request(request))
