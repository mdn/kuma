from __future__ import unicode_literals

import json
from os.path import dirname

from django.test import TestCase
from django.utils.six import StringIO

from .models import Human, HumansTXT

APP_DIR = dirname(__file__)
CONTRIBUTORS_JSON = "%s/fixtures/contributors.json" % APP_DIR


class HumansTest(TestCase):
    def test_split_name(self):
        ht = HumansTXT()

        name = 'buddyl@example.org'
        assert 'buddyl' == ht.split_name(name)

    def test_basic_get_github(self):
        """
        Test that json is parsed and a list is returned
        """
        data = json.load(open(CONTRIBUTORS_JSON, 'rb'))
        ht = HumansTXT()
        humans = ht.get_github(data)
        assert len(humans) == 8

    def test_for_login_name_when_no_name(self):
        """
        Test that when object does't have 'name' it uses the 'login' instead.
        """
        data = json.load(open(CONTRIBUTORS_JSON, 'rb'))
        ht = HumansTXT()
        humans = ht.get_github(data)
        human = Human()
        for h in humans:
            if h.name == "stephaniehobson":
                human = h

        assert human.name == "stephaniehobson"

    def test_write_to_file(self):
        human1 = Human()
        human1.name = "joe"
        human1.website = "http://example.com"

        human2 = Human()
        human2.name = "john"

        humans = []
        humans.append(human1)
        humans.append(human2)

        ht = HumansTXT()
        target = StringIO()
        ht.write_to_file(humans, target, "Banner Message", "Developer")

        output = target.getvalue()
        expected = '\n'.join((
            "Banner Message ",
            "Developer: joe ",
            "Website: http://example.com ",
            "",
            "Developer: john ",
            "",
            ""
        ))

        assert output == expected
