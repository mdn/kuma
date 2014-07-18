import json
import subprocess
import urllib

from django.conf import settings


GITHUB_REPOS = "https://api.github.com/repos/mozilla/kuma/contributors"


class Human:
    def __init__(self):
        self.name = None
        self.website = None


class HumansTXT:
    def generate_file(self):
        githubbers = self.get_github(json.load(urllib.urlopen(GITHUB_REPOS)))
        localizers = self.get_mdn()

        target = open("%s/humans.txt" % settings.HUMANSTXT_ROOT, 'w')

        self.write_to_file(githubbers, target, "Contributors on Github",
            "Developer")
        self.write_to_file(localizers, target, "Localization Contributors",
            "Localizer")

        target.close()

    def write_to_file(self, humans, target, message, role):
        target.write("%s \n" % message)
        for h in humans:
            target.write("%s: %s \n" % (role, h.name.encode('ascii', 'ignore')))
            if(h.website != None):
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
            try:
                human.name = contributor['name']
            except:  # Github doesn't have a name if profile isn't filled out
                human.name = contributor['login']

            try:
                human.website = contributor['blog']
            except:
                human.website = None

            humans.append(human)

        return humans

    def get_mdn(self):
        p = subprocess.Popen("svn log --quiet http://svn.mozilla.org/projects/\
            mdn/trunk/locale/ | grep '^r' | awk '{print $3}' | sort | uniq",
            shell=True, stdout=subprocess.PIPE)
        localizers_list = p.communicate()[0].rstrip().split('\n', -1)

        humans = []
        for localizer in localizers_list:
            human = Human()
            human.name = localizer
            humans.append(human)

        return humans
