import json
from os import makedirs
from os.path import dirname, exists, isdir

import fileinput
from nose.tools import assert_equal, ok_

from django.test import TestCase

from .models import HumansTXT, Human

APP_DIR = dirname(__file__)
CONTRIBUTORS_JSON = "%s/fixtures/contributors.json" % APP_DIR


class HumansTest(TestCase):
    def test_split_name(self):
        ht = HumansTXT()

        name = 'buddyl@example.org'
        assert_equal('buddyl', ht.split_name(name))

    def test_basic_get_github(self):
        """
        Test that json is parsed and a list is returned
        """
        data = json.load(open(CONTRIBUTORS_JSON, 'rb'))
        ht = HumansTXT()
        humans = ht.get_github(data)
        assert_equal(len(humans), 19)

    def test_for_login_name_when_no_name(self):
        """
        Test that when object does't have 'name' it uses the 'login' instead.
        """
        data = json.load(open(CONTRIBUTORS_JSON, 'rb'))
        ht = HumansTXT()
        humans = ht.get_github(data)
        human = Human()
        for h in humans:
            if h.name == "chengwang":
                human = h

        assert_equal(human.name, "chengwang")

    def test_write_to_file(self):
        if not isdir("%s/tmp/" % APP_DIR):
            makedirs("%s/tmp/" % APP_DIR)

        target = open("%s/tmp/humans.txt" % APP_DIR, 'w')
        human1 = Human()
        human1.name = "joe"
        human1.website = "http://example.com"

        human2 = Human()
        human2.name = "john"

        humans = []
        humans.append(human1)
        humans.append(human2)

        ht = HumansTXT()
        ht.write_to_file(humans, target, "Banner Message", "Developer")

        ok_(True, exists("%s/tmp/humans.txt" % APP_DIR))

        message = False
        name = False

        for line in fileinput.input("%s/tmp/humans.txt" % APP_DIR):
            if line == "Banner Message":
                message = True
            if line == "joe":
                name = True

        ok_(True, message)
        ok_(True, name)
