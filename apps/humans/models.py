import json
import urllib
from django.conf import settings

GITHUB_REPOS = "https://github.com/api/v2/json/repos/show/mozilla/kuma/contributors"

class Human:
    def __init__(self):
        self.name = None
        self.website = None

class HumansTXT:
    def generate_file(self):
        githubbers = self.get_github(json.load(urllib.urlopen(GITHUB_REPOS)))
        
        target = open("%s/humans.txt" % settings.HUMANSTXT_ROOT, 'w')

        self.write_to_file(githubbers, target, "Contributors on Github")

        target.close()
    
    def write_to_file(self, humans, target, message):
        target.write("%s \n" % message)
        for h in humans:
            target.write("Developer: %s \n" % h.name.encode('ascii', 'ignore'))
            if(h.website != None):
                target.write("Website: %s \n" % h.website)
            target.write('\n')

    def get_github(self, data=None):
        if not data:
            raw_data = json.load(urllib.urlopen(GITHUB_REPOS))
        else:
            raw_data = data
            
        humans = []
        for contributor in raw_data['contributors']:
            human = Human()
            try:
                human.name = contributor['name']
            except: # Github doesn't have a name if profile isn't filled out
                human.name = contributor['login']

            try:
                human.website = contributor['blog']
            except:
                human.website = None

            humans.append(human)

        return humans
        
      
