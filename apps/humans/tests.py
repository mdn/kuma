"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from os.path import dirname
from os.path import exists
from nose.tools import assert_equal, with_setup, assert_false, eq_, ok_
import json
import fileinput

from humans.models import HumansTXT, Human

APP_DIR = dirname(__file__)
CONTRIBUTORS_JSON = "%s/fixtures/contributors.json" % APP_DIR

class HumansTest(TestCase):
    def test_basic_get_github(self):
        """
        Test that json is parsed and a list is returned
        """
        data = json.load(open(CONTRIBUTORS_JSON, 'rb'))
        ht = HumansTXT()
        humans = ht.get_github(data)
        assert_equal(len(humans), 16)

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
        ht.write_to_file(humans, target, "Banner Message") 

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

