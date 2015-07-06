from django.core.exceptions import MultipleObjectsReturned

from django.contrib.auth.models import AnonymousUser
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError
from django.http import HttpRequest

from nose.tools import eq_, ok_
from nose.plugins.attrib import attr

from kuma.core.urlresolvers import reverse
from kuma.core.utils import get_unique
from kuma.demos.models import Submission
from kuma.demos.tests.test_models import save_valid_submission
from kuma.wiki.models import Document
from kuma.users.tests import UserTransactionTestCase

from .models import ContentFlag


def _mock_request(user=None, ip='192.168.123.123',
                  user_agent='FakeBrowser 1.0'):
    request = HttpRequest()
    request.user = user and user or AnonymousUser()
    request.method = 'GET'
    request.META['REMOTE_ADDR'] = ip
    request.META['HTTP_USER_AGENT'] = user_agent
    return request


class DemoPackageTest(UserTransactionTestCase):
    fixtures = UserTransactionTestCase.fixtures + ['wiki/documents.json']

    def setUp(self):
        super(DemoPackageTest, self).setUp()
        self.user1 = self.user_model.objects.create_user('tester1',
                                                         'tester2@tester.com',
                                                         'tester1')
        self.user2 = self.user_model.objects.create_user('tester2',
                                                         'tester2@tester.com',
                                                         'tester2')

    @attr('bug694544')
    def test_bug694544(self):
        """Bug 694544: unicode character in request details should not break"""
        try:
            request = _mock_request(user_agent=u"Some\xef\xbf\xbdbrowser")

            obj_1 = self.user2
            obj_1_ct = ContentType.objects.get_for_model(obj_1)
            user, ip, user_agent, unique_hash = get_unique(obj_1_ct, obj_1.pk,
                                                           request=request)
        except UnicodeDecodeError:
            ok_(False, "UnicodeDecodeError should not be thrown")

    @attr('bad_multiple')
    def test_bad_multiple_flags(self):
        """
        Force multiple flags, possibly result of race condition,
        ensure graceful handling
        """
        request = _mock_request()

        obj_1 = self.user2
        obj_1_ct = ContentType.objects.get_for_model(obj_1)
        user, ip, user_agent, unique_hash = get_unique(obj_1_ct, obj_1.pk,
                                                       request=request)

        # Create an initial record directly.
        f1 = ContentFlag(content_type=obj_1_ct, object_pk=obj_1.pk,
                         flag_type="Broken thing",
                         ip=ip, user_agent=user_agent, user=user)
        f1.save()

        # Adding a duplicate should be prevented at the model level.
        try:
            f2 = ContentFlag(content_type=obj_1_ct, object_pk=obj_1.pk,
                             flag_type="Broken thing",
                             ip=ip, user_agent=user_agent, user=user)
            f2.save()
        except IntegrityError:
            pass

        # Try flag, which should turn up the single unique record created
        # earlier.
        try:
            flag, created = ContentFlag.objects.flag(
                request=request, object=obj_1, flag_type='notworking',
                explanation="It really not go!")
            ok_(flag is not None)
            ok_(not created)
        except MultipleObjectsReturned:
            ok_(False, "MultipleObjectsReturned should not be raised")

    def test_basic_flag(self):
        """
        Exercise flagging with limit of one per unique
        request per unique object
        """
        # Submit a flag.
        request = _mock_request()
        flag, created = ContentFlag.objects.flag(
            request=request, object=self.user2, flag_type='notworking',
            explanation="It not go.")
        eq_(True, created)

        # One flag instance per unique user
        flag, created = ContentFlag.objects.flag(
            request=request, object=self.user2, flag_type='notworking',
            explanation="It really not go!")
        eq_(False, created)

        # Submit a flag on another object.
        request = _mock_request()
        flag, created = ContentFlag.objects.flag(
            request=request, object=self.user1, flag_type='notworking',
            explanation="It not go.")
        eq_(True, created)

        # Try another unique request
        request = _mock_request(ip='192.168.123.1')
        flag, created = ContentFlag.objects.flag(
            request=request, object=self.user2, flag_type='inappropriate',
            explanation="This is porn.")
        eq_(True, created)

        request = _mock_request(ip='192.168.123.50', user_agent='Mozilla 1.0')
        flag, created = ContentFlag.objects.flag(
            request=request, object=self.user2, flag_type='inappropriate',
            explanation="This is porn.")
        eq_(True, created)

        eq_(4, ContentFlag.objects.count())

    def test_flag_dict(self):
        request = _mock_request()
        objects_to_flag = [
            {'obj': save_valid_submission(),
             'flag_type': 'notworking',
             'explanation': 'I am not good at computer.'},
            {'obj': Document.objects.get(pk=4),
             'flag_type': 'bad',
             'explanation': 'This is in fact not a pipe.'},
            {'obj': Document.objects.get(pk=8),
             'flag_type': 'unneeded',
             'explanation': 'Camels are for Perl, not Python.'},
        ]
        for o in objects_to_flag:
            flag, created = ContentFlag.objects.flag(
                request=request, object=o['obj'], flag_type=o['flag_type'],
                explanation=o['explanation'])
        flag_dict = ContentFlag.objects.flags_by_type()

        # These are translation proxy objects, not strings, so we have
        # to pull them off the model class.
        sub = Submission._meta.verbose_name_plural
        doc = Document._meta.verbose_name_plural

        ok_(sub in flag_dict)
        eq_(1, len(flag_dict[sub]))
        eq_('hello world',
            flag_dict[sub][0].content_object.title)

        ok_(doc in flag_dict)
        eq_(2, len(flag_dict[doc]))
        eq_('le title',
            flag_dict[doc][0].content_object.title)
        eq_('getElementByID',
            flag_dict[doc][1].content_object.title)


class ViewTests(UserTransactionTestCase):
    fixtures = UserTransactionTestCase.fixtures + ['wiki/documents.json']
    localizing_client = True

    def test_flagged_view(self):
        request = _mock_request()
        objects_to_flag = [
            {'obj': save_valid_submission(),
             'flag_type': 'notworking',
             'explanation': 'I am not good at computer.'},
            {'obj': Document.objects.get(pk=4),
             'flag_type': 'bad',
             'explanation': 'This is in fact not a pipe.'},
            {'obj': Document.objects.get(pk=8),
             'flag_type': 'unneeded',
             'explanation': 'Camels are for Perl, not Python.'},
        ]
        for o in objects_to_flag:
            flag, created = ContentFlag.objects.flag(
                request=request, object=o['obj'], flag_type=o['flag_type'],
                explanation=o['explanation'])
        resp = self.client.get(reverse('contentflagging.flagged'))
        eq_(200, resp.status_code)
