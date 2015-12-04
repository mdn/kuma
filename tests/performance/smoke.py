import os

from locust import HttpLocust, TaskSet, task


class SmokeBehavior(TaskSet):
    """
    Request behavior that represents some standard production behavior.
    Tasks uris are hard-coded for now, but could be stored or even dynamically
    generated later.
    See https://bugzil.la/1186085
    """

    def on_start(self):
        locust_host = os.environ.get('LOCUST_HOST', 'developer.allizom.org')
        self.client.headers['Host'] = locust_host

    @task(weight=265)
    def home(self):
        self.client.get('/en-US/')

    @task(weight=185)
    def midas(self):
        self.client.get('/en-US/docs/Mozilla/Projects/Midas/Security_preferences')

    @task(weight=143)
    def js(self):
        self.client.get('/en-US/docs/Web/JavaScript')

    @task(weight=123)
    def js_ref_foreach(self):
        self.client.get('/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/forEach')

    @task(weight=117)
    def media_queries(self):
        self.client.get('/en-US/docs/Web/Guide/CSS/Media_queries')

    @task(weight=49)
    def learn_zone_js_basics(self):
        self.client.get('/en-US/Learn/Getting_started_with_the_web/JavaScript_basics')

    @task(weight=30)
    def learn_zone_home(self):
        self.client.get('/en-US/Learn')

    @task(weight=34)
    def ru_home(self):
        self.client.get('/ru/')

    @task(weight=20)
    def zh_CN_js(self):
        self.client.get('/zh-CN/docs/Web/JavaScript')


class SmokeLocust(HttpLocust):
    task_set = SmokeBehavior
