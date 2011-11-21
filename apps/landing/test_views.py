from nose.tools import eq_, ok_
from nose.plugins.skip import SkipTest
from mock import patch
from pyquery import PyQuery as pq
import test_utils
from waffle.models import Switch

from sumo.tests import LocalizingClient
from sumo.urlresolvers import reverse


class LearnViewsTest(test_utils.TestCase):

    def setUp(self):
        self.client = LocalizingClient()

    def test_learn(self):
        url = reverse('landing.views.learn')
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

    def test_learn_html(self):
        url = reverse('landing.views.learn_html')
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

    def test_learn_css(self):
        url = reverse('landing.views.learn_css')
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

    def test_learn_javascript(self):
        url = reverse('landing.views.learn_javascript')
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)


class LandingViewsTest(test_utils.TestCase):
    fixtures = ['test_data.json', ]

    def setUp(self):
        self.client = LocalizingClient()

    def test_home(self):
        url = reverse('landing.views.home')
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

        doc = pq(r.content)
        dev_mdc_link = doc.find('a#dev-mdc-link')
        ok_(dev_mdc_link)

    def test_addons(self):
        url = reverse('landing.views.addons')
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

    def test_mozilla(self):
        url = reverse('landing.views.mozilla')
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

    def test_mobile(self):
        url = reverse('landing.views.mobile')
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

    def test_web(self):
        url = reverse('landing.views.web')
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

    def test_search(self):
        raise SkipTest('Search test disabled until we switch to kuma wiki')
        url = reverse('landing.views.search')
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

    def test_promote_buttons(self):
        url = reverse('landing.views.promote_buttons')
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

    def test_discussion(self):
        url = reverse('landing.views.discussion')
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

    def test_discussion_archive_link_waffled(self):
        url = reverse('landing.views.discussion')
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

        doc = pq(r.content)
        phpbb_link = doc.find('a#forum-archive-link')
        eq_('/forums', phpbb_link.attr('href'))

        s = Switch.objects.create(name='static_forums', active=True)
        s.save()
        r = self.client.get(url, follow=True)
        doc = pq(r.content)
        phpbb_link = doc.find('a#forum-archive-link')
        eq_('/forum-archive/', phpbb_link.attr('href'))

    def test_forum_archive(self):
        url = reverse('landing.views.forum_archive')
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)


class AppsViewsTest(test_utils.TestCase):

    def setUp(self):
        self.client = LocalizingClient()

    def test_apps_menu_item(self):
        url = reverse('landing.views.home')
        r = self.client.get(url)
        eq_(200, r.status_code)

        doc = pq(r.content)
        nav_sub_topics = doc.find('ul#nav-sub-topics')
        ok_(nav_sub_topics)
        apps_item = nav_sub_topics.find('li#nav-sub-apps')
        eq_([], apps_item)

        s = Switch.objects.create(name='apps_landing', active=True)
        s.save()
        r = self.client.get(url)
        eq_(200, r.status_code)
        doc = pq(r.content)
        nav_sub_topics = doc.find('ul#nav-sub-topics')
        ok_(nav_sub_topics)
        apps_item = nav_sub_topics.find('li#nav-sub-apps')
        eq_('Apps', apps_item.text())

    def test_apps(self):
        url = reverse('landing.views.apps')
        r = self.client.get(url)
        eq_(404, r.status_code)

        s = Switch.objects.create(name='apps_landing', active=True)
        s.save()
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)
        doc = pq(r.content)
        responsys_form = doc.find('form.fm-subscribe')
        eq_(reverse('apps_subscription', locale='en-US'), responsys_form.attr('action'))

    @patch('landing.views.responsys.subscribe')
    def test_apps_subscription(self, subscribe):
        subscribe.return_value = True
        s = Switch.objects.create(name='apps_landing', active=True)
        s.save()
        url = reverse('landing.views.apps_subscription')
        r = self.client.post(url, {'format': 'html', 'email': 'testuser@test.com', 'agree': 'checked'}, follow=True)
        eq_(200, r.status_code)
        # assert thank you message
        self.assertContains(r, 'Thank you')
        # TODO: figure out why the mock doesn't work?
        # subscribe.assert_called_once_with('APP_DEV_BREAK', 'testuser@test.com', format='text')


    @patch('landing.views.responsys.subscribe')
    def test_apps_subscription_bad_values(self, subscribe):
        subscribe.return_value = True
        s = Switch.objects.create(name='apps_landing', active=True)
        s.save()
        url = reverse('landing.views.apps_subscription')
        r = self.client.post(url, {'format': 1, 'email': 'nope'})
        eq_(200, r.status_code)
        # assert error
        self.assertContains(r, 'Enter a valid e-mail address.')
        self.assertContains(r, 'Select a valid choice.')
        self.assertContains(r, 'You must agree to the privacy policy.')
