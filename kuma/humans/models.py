from __future__ import with_statement
import json
import os
import subprocess
import urllib

from django.conf import settings


GITHUB_REPOS = "https://api.github.com/repos/mozilla/kuma/contributors"


class Human(object):
    def __init__(self):
        self.name = None
        self.website = None


class HumansTXT(object):

    def generate_file(self):
        githubbers = self.get_github(json.load(urllib.urlopen(GITHUB_REPOS)))
        localizers = self.get_mdn()
        path = os.path.join(settings.HUMANSTXT_ROOT, "humans.txt")

        with open(path, 'w') as target:
            self.write_to_file(githubbers, target,
                               "Contributors on Github", "Developer")
            self.write_to_file(localizers, target,
                               "Localization Contributors", "Localizer")

    def write_to_file(self, humans, target, message, role):
        target.write("%s \n" % message)
        for h in humans:
            target.write("%s: %s \n" %
                         (role, h.name.encode('ascii', 'ignore')))
            if h.website is not None:
                target.write("Website: %s \n" % h.website)
                target.write('\n')
        target.write('\n')

    def get_github(self, data=None):
        if not data:
            raw_data = json.load(urllib.urlopen(GITHUB_REPOS))
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

    def get_mdn(self):
        p = subprocess.Popen(
            "svn log --quiet http://svn.mozilla.org/projects/\
            mdn/trunk/locale/ | grep '^r' | awk '{print $3}' | sort | uniq",
            shell=True, stdout=subprocess.PIPE)
        localizers_list = p.communicate()[0].rstrip().split('\n', -1)

        humans = []
        for localizer in localizers_list:
            human = Human()
            human.name = self.split_name(localizer)
            humans.append(human)

        return humans
