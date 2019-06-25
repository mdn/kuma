from __future__ import unicode_literals
from __future__ import with_statement

import json
import os

from django.conf import settings
from django.utils.six.moves.urllib.request import urlopen

GITHUB_REPOS = "https://api.github.com/repos/mozilla/kuma/contributors"


class Human(object):
    def __init__(self):
        self.name = None
        self.website = None


class HumansTXT(object):

    def generate_file(self):
        githubbers = self.get_github(json.load(urlopen(GITHUB_REPOS)))
        path = os.path.join(settings.HUMANSTXT_ROOT, "humans.txt")
        with open(path, 'w') as target:
            self.write_to_file(githubbers, target,
                               "Contributors on GitHub", "Developer")

    def write_to_file(self, humans, target, message, role):
        target.write("%s \n" % message)
        for h in humans:
            target.write("%s: %s \n" % (role, h.name))
            if h.website is not None:
                target.write("Website: %s \n" % h.website)
                target.write('\n')
        target.write('\n')

    def get_github(self, data=None):
        if not data:
            raw_data = json.load(urlopen(GITHUB_REPOS))
        else:
            raw_data = data

        humans = []
        for contributor in raw_data:
            human = Human()
            human.name = contributor.get('name', contributor['login'])
            human.website = contributor.get('blog', None)
            humans.append(human)

        return humans

    def split_name(self, name):
        if '@' in name:
            name = name.split('@')[0]

        return name
