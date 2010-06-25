from nose.tools import eq_
from pyquery import PyQuery as pq

from questions.models import Question
from questions.tests import TestCaseBase, post, get


class AnswersTemplateTestCase(TestCaseBase):
    """Test the Answers template."""
    def setUp(self):
        super(AnswersTemplateTestCase, self).setUp()

        self.client.login(username='jsocol', password='testpass')
        self.question = Question.objects.all()[0]

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
        new_answer.delete()

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
