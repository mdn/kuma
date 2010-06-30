from nose.tools import eq_
from pyquery import PyQuery as pq

from sumo.urlresolvers import reverse
from sumo.helpers import urlparams
from questions.models import Question, Answer
from questions.tests import TestCaseBase, post, get


class AnswersTemplateTestCase(TestCaseBase):
    """Test the Answers template."""
    def setUp(self):
        super(AnswersTemplateTestCase, self).setUp()

        self.client.login(username='jsocol', password='testpass')
        self.question = Question.objects.all()[0]
        self.answer = self.question.answers.all()[0]

    def tearDown(self):
        super(AnswersTemplateTestCase, self).tearDown()

        self.client.logout()

    def test_answer(self):
        """Posting a valid answer inserts it."""
        num_answers = self.question.answers.count()
        content = 'lorem ipsum dolor sit amet'
        response = post(self.client, 'questions.reply',
                        {'content': content},
                        args=[self.question.id])

        eq_(1, len(response.redirect_chain))
        eq_(num_answers + 1, self.question.answers.count())

        new_answer = self.question.answers.order_by('-created')[0]
        eq_(content, new_answer.content)

    def test_empty_answer(self):
        """Posting an empty answer shows error."""
        response = post(self.client, 'questions.reply', {'content': ''},
                        args=[self.question.id])

        doc = pq(response.content)
        error_msg = doc('ul.errorlist li a')[0]
        eq_(error_msg.text, 'Please provide content.')

    def test_short_answer(self):
        """Posting a short answer shows error."""
        response = post(self.client, 'questions.reply', {'content': 'lor'},
                        args=[self.question.id])

        doc = pq(response.content)
        error_msg = doc('ul.errorlist li a')[0]
        eq_(error_msg.text, 'Your content is too short (3 characters). ' +
                            'It must be at least 5 characters.')

    def test_long_answer(self):
        """Post a long answer shows error."""

        # Set up content length to 10,001 characters
        content = ''
        for i in range(1000):
            content += '1234567890'
        content += '1'

        response = post(self.client, 'questions.reply', {'content': content},
                        args=[self.question.id])

        doc = pq(response.content)
        error_msg = doc('ul.errorlist li a')[0]
        eq_(error_msg.text, 'Please keep the length of your content to ' +
                            '10000 characters or less. It is currently ' +
                            '10001 characters.')

    def test_solution(self):
        """Test accepting a solution."""
        response = get(self.client, 'questions.answers',
                       args=[self.question.id])
        doc = pq(response.content)
        eq_(0, len(doc('div.solution')))

        answer = self.question.answers.all()[0]
        response = post(self.client, 'questions.solution',
                        args=[self.question.id, answer.id])
        doc = pq(response.content)
        eq_(1, len(doc('div.solution')))
        eq_('answer-%s' % answer.id, doc('li.solution')[0].attrib['id'])

        self.question.solution = None
        self.question.save()

    def test_only_owner_can_accept_solution(self):
        """Make sure non-owner can't mark solution."""
        response = get(self.client, 'questions.answers',
                       args=[self.question.id])
        doc = pq(response.content)
        eq_(1, len(doc('input[name="solution"]')))

        self.client.logout()
        self.client.login(username='pcraciunoiu', password='testpass')
        response = get(self.client, 'questions.answers',
                       args=[self.question.id])
        doc = pq(response.content)
        eq_(0, len(doc('input[name="solution"]')))

        answer = self.question.answers.all()[0]
        response = post(self.client, 'questions.solution',
                        args=[self.question.id, answer.id])
        eq_(403, response.status_code)

    def test_question_vote_GET(self):
        """Attempting to vote with HTTP GET returns a 405."""
        response = get(self.client, 'questions.vote',
                       args=[self.question.id])
        eq_(405, response.status_code)

    def common_vote(self):
        """Helper method for question vote tests."""
        # Check that there are no votes and vote form renders
        response = get(self.client, 'questions.answers',
                       args=[self.question.id])
        doc = pq(response.content)
        eq_('0 people', doc('div.have-problem mark')[0].text)
        eq_(1, len(doc('div.me-too form')))

        # Vote
        post(self.client, 'questions.vote', args=[self.question.id])

        # Check that there is 1 vote and vote form doesn't render
        response = get(self.client, 'questions.answers',
                       args=[self.question.id])
        doc = pq(response.content)
        eq_('1 person', doc('div.have-problem mark')[0].text)
        eq_(0, len(doc('div.me-too form')))

        # Voting again (same user) should not increment vote count
        post(self.client, 'questions.vote', args=[self.question.id])
        response = get(self.client, 'questions.answers',
                       args=[self.question.id])
        doc = pq(response.content)
        eq_('1 person', doc('div.have-problem mark')[0].text)

    def test_question_authenticated_vote(self):
        """Authenticated user vote."""
        # Common vote test
        self.common_vote()

    def test_question_anonymous_vote(self):
        """Anonymous user vote."""
        # Log out
        self.client.logout()

        # Common vote test
        self.common_vote()

    def common_answer_vote(self):
        """Helper method for answer vote tests."""
        # Check that there are no votes and vote form renders
        response = get(self.client, 'questions.answers',
                       args=[self.question.id])
        doc = pq(response.content)
        eq_('0 out of 0 people', doc('#answer-1 div.helpful mark')[0].text)
        eq_(1, len(doc('form.helpful input[name="helpful"]')))

        # Vote
        post(self.client, 'questions.answer_vote', {'helpful': 'y'},
             args=[self.question.id, self.answer.id])

        # Check that there is 1 vote and vote form doesn't render
        response = get(self.client, 'questions.answers',
                       args=[self.question.id])
        doc = pq(response.content)

        eq_('1 out of 1 person', doc('#answer-1 div.helpful mark')[0].text)
        eq_(0, len(doc('form.helpful input[name="helpful"]')))

        # Voting again (same user) should not increment vote count
        post(self.client, 'questions.answer_vote', {'helpful': 'y'},
             args=[self.question.id, self.answer.id])
        doc = pq(response.content)
        eq_('1 out of 1 person', doc('#answer-1 div.helpful mark')[0].text)

    def test_answer_authenticated_vote(self):
        """Authenticated user answer vote."""
        # log in as rrosario (didn't ask or answer question)
        self.client.logout()
        self.client.login(username='rrosario', password='testpass')

        # Common vote test
        self.common_answer_vote()

    def test_answer_anonymous_vote(self):
        """Anonymous user answer vote."""
        # Log out
        self.client.logout()

        # Common vote test
        self.common_answer_vote()

    def test_answer_score(self):
        """Test the helpful replies score."""
        self.client.logout()

        # A helpful vote
        post(self.client, 'questions.answer_vote', {'helpful': 'y'},
             args=[self.question.id, self.answer.id])

        # Verify score (should be 1)
        response = get(self.client, 'questions.answers',
                       args=[self.question.id])
        doc = pq(response.content)
        eq_('1', doc('div.other-helpful span.votes')[0].text)

        # A non-helpful vote
        self.client.login(username='rrosario', password='testpass')
        post(self.client, 'questions.answer_vote', {'not-helpful': 'y'},
             args=[self.question.id, self.answer.id])

        # Verify score (should be 0 now)
        response = get(self.client, 'questions.answers',
                       args=[self.question.id])
        doc = pq(response.content)
        eq_('0', doc('div.other-helpful span.votes')[0].text)


class QuestionsTemplateTestCase(TestCaseBase):

    def test_all_filter_highlight(self):
        response = get(self.client, 'questions.questions')
        doc = pq(response.content)
        eq_('active', doc('div#filter ul li')[3].attrib['class'])
        eq_('question-1', doc('ol.questions li')[0].attrib['id'])

    def test_no_reply_filter(self):
        url_ = urlparams(reverse('questions.questions'),
                         filter='no-replies')
        response = self.client.get(url_)
        doc = pq(response.content)
        eq_('active', doc('div#filter ul li')[-1].attrib['class'])
        eq_('question-2', doc('ol.questions li')[0].attrib['id'])

    def test_solved_filter(self):
        # initially there should be no solved answers
        url_ = urlparams(reverse('questions.questions'),
                         filter='solved')
        response = self.client.get(url_)
        doc = pq(response.content)
        eq_('active', doc('div#filter ul li')[5].attrib['class'])
        eq_(0, len(doc('ol.questions li')))

        # solve one question then verify that it shows up
        answer = Answer.objects.all()[0]
        answer.question.solution = answer
        answer.question.save()
        response = self.client.get(url_)
        doc = pq(response.content)
        eq_(1, len(doc('ol.questions li')))
        eq_('question-%s' % answer.question.id,
            doc('ol.questions li')[0].attrib['id'])

    def test_unsolved_filter(self):
        # initially there should be 2 unsolved answers
        url_ = urlparams(reverse('questions.questions'),
                         filter='unsolved')
        response = self.client.get(url_)
        doc = pq(response.content)
        eq_('active', doc('div#filter ul li')[4].attrib['class'])
        eq_(2, len(doc('ol.questions li')))

        # solve one question then verify that it doesn't show up
        answer = Answer.objects.all()[0]
        answer.question.solution = answer
        answer.question.save()
        response = self.client.get(url_)
        doc = pq(response.content)
        eq_(1, len(doc('ol.questions li')))
        eq_(0, len(doc('ol.questions li#question-%s' % answer.question.id)))

    def _my_contributions_test_helper(self, username, expected_qty):
        url_ = urlparams(reverse('questions.questions'),
                         filter='my-contributions')
        self.client.login(username=username, password="testpass")
        response = self.client.get(url_)
        doc = pq(response.content)
        eq_('active', doc('div#filter ul li')[7].attrib['class'])
        eq_(expected_qty, len(doc('ol.questions li')))

    def test_my_contributions_filter(self):
        # jsocol should have 2 questions in his contributions
        self._my_contributions_test_helper('jsocol', 2)

        # pcraciunoiu should have 1 questions in his contributions'
        self._my_contributions_test_helper('pcraciunoiu', 1)

        # rrosario should have 0 questions in his contributions
        self._my_contributions_test_helper('rrosario', 0)
