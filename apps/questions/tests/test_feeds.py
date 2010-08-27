from datetime import datetime

from django.core.cache import cache

from nose.tools import eq_
from taggit.models import Tag
from pyquery import PyQuery as pq

from sumo.urlresolvers import reverse
from sumo.helpers import urlparams
from questions.feeds import QuestionsFeed, TaggedQuestionsFeed
from questions.models import Question, UNCONFIRMED
from questions.tests import TaggingTestCaseBase


class ForumTestFeedSorting(TaggingTestCaseBase):

    def test_tagged_feed(self):
        """Test the tagged feed."""
        tag = Tag.objects.get(slug='green')
        items = TaggedQuestionsFeed().items(tag)
        eq_(2, items[0].id)
        eq_(1, len(items))

        cache.clear()

        q = Question.objects.get(pk=1)
        q.tags.add('green')
        q.updated = datetime.now()
        q.save()
        items = TaggedQuestionsFeed().items(tag)
        eq_(1, items[0].id)
        eq_(2, len(items))

    def test_tagged_feed_link(self):
        """Make sure the tagged feed is discoverable on the questions page."""
        url = urlparams(reverse('questions.questions'), tagged='green')
        response = self.client.get(url)
        doc = pq(response.content)
        feed_links = doc('link[type="application/atom+xml"]')
        eq_(2, len(feed_links))
        eq_('Recently updated questions', feed_links[0].attrib['title'])
        eq_('/en-US/questions/feed', feed_links[0].attrib['href'])
        eq_('Recently updated questions tagged green',
            feed_links[1].attrib['title'])
        eq_('/en-US/questions/tagged/green/feed',
            feed_links[1].attrib['href'])

    def test_no_unconfirmed_questions(self):
        """Ensure that unconfirmed questions don't appear in the feed."""
        q = Question(title='Test Question', content='Lorem Ipsum Dolor',
                     creator_id=118533, status=UNCONFIRMED)
        q.save()
        assert q.id not in [x.id for x in QuestionsFeed().items()]
