import json
from datetime import datetime, timedelta

from django.contrib.auth.models import User, Permission

from nose.plugins.skip import SkipTest
from nose.tools import eq_
from pyquery import PyQuery as pq

from notifications import check_watch, create_watch
from questions.models import Question, Answer, QuestionVote, UNCONFIRMED
from questions.tests import TestCaseBase, TaggingTestCaseBase, tags_eq
from questions.views import UNAPPROVED_TAG, NO_TAG
from questions.tasks import cache_top_contributors
from sumo.urlresolvers import reverse
from sumo.helpers import urlparams
from sumo.tests import get, post
from upload.models import ImageAttachment


class AnswersTemplateTestCase(TestCaseBase):
    """Test the Answers template."""
    def setUp(self):
        super(AnswersTemplateTestCase, self).setUp()

        self.client.login(username='jsocol', password='testpass')
        self.question = Question.objects.get(pk=1)
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

    def test_answer_upload(self):
        """Posting answer attaches an existing uploaded image to the answer."""

        f = open('apps/upload/tests/media/test.jpg')
        post(self.client, 'upload.up_image_async', {'image': f},
             args=['questions.Question', self.question.id])
        f.close()

        content = 'lorem ipsum dolor sit amet'
        response = post(self.client, 'questions.reply',
                        {'content': content},
                        args=[self.question.id])
        eq_(200, response.status_code)

        new_answer = self.question.answers.order_by('-created')[0]
        eq_(1, new_answer.images.count())
        image = new_answer.images.all()[0]
        message = 'File name "%s" does not contain "test"' % image.file.name
        assert 'test' in image.file.name, message
        eq_('jsocol', image.creator.username)

        # Clean up
        ImageAttachment.objects.all().delete()

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
                            '10,000 characters or less. It is currently ' +
                            '10,001 characters.')

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

    def test_delete_question_without_permissions(self):
        """Deleting a question without permissions redirects to login."""
        response = get(self.client, 'questions.delete',
                       args=[self.question.id])
        redirect = response.redirect_chain[0]
        eq_(302, redirect[1])
        eq_('http://testserver/tiki-login.php?next=/en-US/questions/1/delete',
            redirect[0])

        response = post(self.client, 'questions.delete',
                        args=[self.question.id])
        redirect = response.redirect_chain[0]
        eq_(302, redirect[1])
        eq_('http://testserver/tiki-login.php?next=/en-US/questions/1/delete',
            redirect[0])

    def test_delete_question_with_permissions(self):
        """Deleting a question with permissions."""
        self.client.login(username='admin', password='testpass')
        response = get(self.client, 'questions.delete',
                       args=[self.question.id])
        eq_(200, response.status_code)

        response = post(self.client, 'questions.delete',
                        args=[self.question.id])
        eq_(0, Question.objects.filter(pk=self.question.id).count())

    def test_delete_answer_without_permissions(self):
        """Deleting an answer without permissions redirects to login."""
        answer = self.question.last_answer
        response = get(self.client, 'questions.delete_answer',
                       args=[self.question.id, answer.id])
        redirect = response.redirect_chain[0]
        eq_(302, redirect[1])
        eq_('http://testserver/tiki-login.php?next=/en-US/' + \
            'questions/1/delete/1',
            redirect[0])

        response = post(self.client, 'questions.delete_answer',
                        args=[self.question.id, answer.id])
        redirect = response.redirect_chain[0]
        eq_(302, redirect[1])
        eq_('http://testserver/tiki-login.php?next=/en-US/' + \
            'questions/1/delete/1',
            redirect[0])

    def test_delete_answer_with_permissions(self):
        """Deleting an answer with permissions."""
        answer = self.question.last_answer
        self.client.login(username='admin', password='testpass')
        response = get(self.client, 'questions.delete_answer',
                       args=[self.question.id, answer.id])
        eq_(200, response.status_code)

        response = post(self.client, 'questions.delete_answer',
                        args=[self.question.id, answer.id])
        eq_(0, Answer.objects.filter(pk=self.question.id).count())

    def test_edit_answer_without_permission(self):
        """Editing an answer without permissions returns a 403.

        The edit link shouldn't show up on the Answers page."""
        response = get(self.client, 'questions.answers',
                       args=[self.question.id])
        doc = pq(response.content)
        eq_(0, len(doc('ol.answers a.edit')))

        answer = self.question.last_answer
        response = get(self.client, 'questions.edit_answer',
                       args=[self.question.id, answer.id])
        eq_(403, response.status_code)

        content = 'New content for answer'
        response = post(self.client, 'questions.edit_answer',
                        {'content': content},
                        args=[self.question.id, answer.id])
        eq_(403, response.status_code)

    def test_edit_answer_with_permissions(self):
        """Editing an answer with permissions.

        The edit link should show up on the Answers page."""
        self.client.login(username='admin', password='testpass')

        response = get(self.client, 'questions.answers',
                       args=[self.question.id])
        doc = pq(response.content)
        eq_(1, len(doc('ol.answers a.edit')))

        answer = self.question.last_answer
        response = get(self.client, 'questions.edit_answer',
                       args=[self.question.id, answer.id])
        eq_(200, response.status_code)

        content = 'New content for answer'
        response = post(self.client, 'questions.edit_answer',
                        {'content': content},
                        args=[self.question.id, answer.id])
        eq_(content, Answer.objects.get(pk=answer.id).content)

    def test_answer_creator_can_edit(self):
        """The creator of an answer can edit his/her answer."""
        self.client.login(username='rrosario', password='testpass')

        # Initially there should be no edit links
        response = get(self.client, 'questions.answers',
                       args=[self.question.id])
        doc = pq(response.content)
        eq_(0, len(doc('ol.answers a.edit')))

        # Add an answer and verify the edit link shows up
        content = 'lorem ipsum dolor sit amet'
        response = post(self.client, 'questions.reply',
                        {'content': content},
                        args=[self.question.id])
        doc = pq(response.content)
        eq_(1, len(doc('ol.answers a.edit')))
        new_answer = self.question.answers.order_by('-created')[0]
        eq_(1, len(doc('#answer-%s a.edit' % new_answer.id)))

        # Make sure it can be edited
        content = 'New content for answer'
        response = post(self.client, 'questions.edit_answer',
                        {'content': content},
                        args=[self.question.id, new_answer.id])
        eq_(200, response.status_code)

        # Now lock it and make sure it can't be edited
        self.question.is_locked = True
        self.question.save()
        response = post(self.client, 'questions.edit_answer',
                        {'content': content},
                        args=[self.question.id, new_answer.id])
        eq_(403, response.status_code)

    def test_lock_question_without_permissions(self):
        """Trying to lock a question without permission redirects to login."""
        q = self.question
        response = post(self.client, 'questions.lock', args=[q.id])
        redirect = response.redirect_chain[0]
        eq_(302, redirect[1])
        eq_('http://testserver/tiki-login.php?next=/en-US/' + \
            'questions/1/lock',
            redirect[0])

    def test_lock_question_with_permissions_GET(self):
        """Trying to lock a question via HTTP GET."""
        response = get(self.client, 'questions.lock', args=[self.question.id])
        eq_(405, response.status_code)

    def test_lock_question_with_permissions_POST(self):
        """Locking questions with permissions via HTTP POST."""
        self.client.login(username='admin', password='testpass')
        q = self.question
        response = post(self.client, 'questions.lock', args=[q.id])
        eq_(200, response.status_code)
        eq_(True, Question.objects.get(pk=q.pk).is_locked)
        doc = pq(response.content)
        eq_(1, len(doc('#question div.badges span.locked')))

        # now unlock it
        response = post(self.client, 'questions.lock', args=[q.id])
        eq_(200, response.status_code)
        eq_(False, Question.objects.get(pk=q.pk).is_locked)
        doc = pq(response.content)
        eq_(0, len(doc('#question div.badges span.locked')))

    def test_reply_to_locked_question_403(self):
        """Locked questions can't be answered."""
        q = self.question
        q.is_locked = True
        q.save()
        response = post(self.client, 'questions.reply',
                        {'content': 'just testing'}, args=[q.id])
        eq_(403, response.status_code)

    def test_vote_locked_question_403(self):
        """Locked questions can't be voted on."""
        q = self.question
        q.is_locked = True
        q.save()
        self.client.login(username='rrosario', password='testpass')
        response = post(self.client, 'questions.vote', args=[q.id])
        eq_(403, response.status_code)

    def test_vote_answer_to_locked_question_403(self):
        """Answers to locked questions can't be voted on."""
        q = self.question
        q.is_locked = True
        q.save()
        self.client.login(username='rrosario', password='testpass')
        response = post(self.client, 'questions.answer_vote',
                        {'helpful': 'y'}, args=[q.id, self.answer.id])
        eq_(403, response.status_code)

    def test_watch_GET_405(self):
        """Watch replies with HTTP GET results in 405."""
        self.client.login(username='rrosario', password='testpass')
        response = get(self.client, 'questions.watch',
                       args=[self.question.id])
        eq_(405, response.status_code)

    def test_unwatch_GET_405(self):
        """Unwatch replies with HTTP GET results in 405."""
        self.client.login(username='rrosario', password='testpass')
        response = get(self.client, 'questions.unwatch',
                       args=[self.question.id])
        eq_(405, response.status_code)

    def test_watch_replies(self):
        """Watch a question for replies."""
        self.client.logout()
        post(self.client, 'questions.watch',
             {'email': 'somebody@nowhere.com', 'event_type': 'reply'},
             args=[self.question.id])
        assert check_watch(Question, self.question.id, 'somebody@nowhere.com',
                           'reply'), 'Watch was not created'

    def test_watch_replies_logged_in(self):
        """Watch a question for replies (logged in)."""
        self.client.login(username='rrosario', password='testpass')
        user = User.objects.get(username='rrosario')
        post(self.client, 'questions.watch',
             {'email': 'user118577@nowhere.com', 'event_type': 'reply'},
             args=[self.question.id])
        assert check_watch(Question, self.question.id, user.email,
                           'reply'), 'Watch was not created'

    def test_watch_solution(self):
        """Watch a question for solution."""
        self.client.logout()
        post(self.client, 'questions.watch',
             {'email': 'somebody@nowhere.com', 'event_type': 'solution'},
             args=[self.question.id])
        assert check_watch(Question, self.question.id, 'somebody@nowhere.com',
                           'solution'), 'Watch was not created'

    def test_unwatch(self):
        """Unwatch a question."""
        self.client.login(username='rrosario', password='testpass')
        user = User.objects.get(username='rrosario')
        create_watch(Question, self.question.id, user.email, 'solution')
        post(self.client, 'questions.unwatch', args=[self.question.id])
        assert not check_watch(Question, self.question.id, user.email,
                               'solution'), 'Watch was not destroyed'

    def test_watch_solution_and_replies(self):
        """User subscribes to solution and replies: page doesn't break"""
        self.client.login(username='rrosario', password='testpass')
        user = User.objects.get(username='rrosario')
        create_watch(Question, self.question.id, user.email, 'reply')
        create_watch(Question, self.question.id, user.email, 'solution')
        response = get(self.client, 'questions.answers',
                       args=[self.question.id])
        eq_(200, response.status_code)

    def test_preview_answer(self):
        """Preview an answer."""
        num_answers = self.question.answers.count()
        content = 'Awesome answer.'
        response = post(self.client, 'questions.reply',
                        {'content': content, 'preview': 'any string'},
                        args=[self.question.id])
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(content, doc('#answer-preview div.content').text())
        eq_(num_answers, self.question.answers.count())


class TaggedQuestionsTestCase(TaggingTestCaseBase):
    """Questions/answers template tests that require tagged questions."""

    def setUp(self):
        super(TaggedQuestionsTestCase, self).setUp()

        q = Question.objects.get(pk=1)
        q.tags.add('green')

    def test_related_list(self):
        """Test that related Questions appear in the list."""

        raise SkipTest

        question = Question.objects.get(pk=1)
        response = get(self.client, 'questions.answers',
                       args=[question.id])
        doc = pq(response.content)
        eq_(1, len(doc('ul.related li')))


class TaggingViewTestsAsTagger(TaggingTestCaseBase):
    """Tests for views that add and remove tags, logged in as someone who can
    add and remove but not create tags

    Also hits the tag-related parts of the answer template.

    """
    def setUp(self):
        super(TaggingViewTestsAsTagger, self).setUp()

        # Assign tag_question permission to the "tagger" user.
        # Would be nice to have a natural key for doing this via a fixture.
        self._can_tag = Permission.objects.get_by_natural_key('tag_question',
                                                              'questions',
                                                              'question')
        self._user = User.objects.get(username='tagger')
        self._user.user_permissions.add(self._can_tag)

        self.client.login(username='tagger', password='testpass')

    def tearDown(self):
        self.client.logout()
        self._user.user_permissions.remove(self._can_tag)
        super(TaggingViewTestsAsTagger, self).tearDown()

    # add_tag view:

    def test_add_tag_get_method(self):
        """Assert GETting the add_tag view redirects to the answers page."""
        response = self.client.get(_add_tag_url())
        url = 'http://testserver%s' % reverse('questions.answers',
                                              kwargs={'question_id': 1},
                                              force_locale=True)
        self.assertRedirects(response, url)

    def test_add_nonexistent_tag(self):
        """Assert adding a nonexistent tag sychronously shows an error."""
        response = self.client.post(_add_tag_url(),
                                    data={'tag-name': 'nonexistent tag'})
        self.assertContains(response, UNAPPROVED_TAG)

    def test_add_existent_tag(self):
        """Test adding a tag, case insensitivity, and space stripping."""
        response = self.client.post(_add_tag_url(),
                                    data={'tag-name': ' PURplepurplepurple '},
                                    follow=True)
        self.assertContains(response, 'purplepurplepurple')

    def test_add_no_tag(self):
        """Make sure adding a blank tag shows an error message."""
        response = self.client.post(_add_tag_url(),
                                    data={'tag-name': ''})
        self.assertContains(response, NO_TAG)

    # add_tag_async view:

    def test_add_async_nonexistent_tag(self):
        """Assert adding an nonexistent tag yields an AJAX error."""
        response = self.client.post(_add_async_tag_url(),
                                    data={'tag-name': 'nonexistent tag'},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertContains(response, UNAPPROVED_TAG, status_code=400)

    def test_add_async_existent_tag(self):
        """Assert adding an unapplied tag yields an AJAX error."""
        response = self.client.post(_add_async_tag_url(),
                                    data={'tag-name': ' PURplepurplepurple '},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertContains(response, 'canonicalName')
        eq_([t.name for t in Question.objects.get(pk=1).tags.all()],
            ['purplepurplepurple'])  # Test the backend since we don't have a
                                     # newly rendered page to rely on.

    def test_add_async_no_tag(self):
        """Assert adding an empty tag asynchronously yields an AJAX error."""
        response = self.client.post(_add_async_tag_url(),
                                    data={'tag-name': ''},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertContains(response, NO_TAG, status_code=400)

    # remove_tag view:

    def test_remove_applied_tag(self):
        """Assert removing an applied tag succeeds."""
        response = self.client.post(_remove_tag_url(),
                                    data={'remove-tag-colorless': 'dummy'})
        self._assert_redirects_to_question_2(response)
        eq_([t.name for t in Question.objects.get(pk=2).tags.all()], ['green'])

    def test_remove_unapplied_tag(self):
        """Test removing an unapplied tag fails silently."""
        response = self.client.post(_remove_tag_url(),
                                    data={'remove-tag-lemon': 'dummy'})
        self._assert_redirects_to_question_2(response)

    def test_remove_no_tag(self):
        """Make sure removing with no params provided redirects harmlessly."""
        response = self.client.post(_remove_tag_url(),
                                    data={})
        self._assert_redirects_to_question_2(response)

    def _assert_redirects_to_question_2(self, response):
        url = 'http://testserver%s' % reverse('questions.answers',
                                              kwargs={'question_id': 2},
                                              force_locale=True)
        self.assertRedirects(response, url)

    # remove_tag_async view:

    def test_remove_async_applied_tag(self):
        """Assert taking a tag off a question works."""
        response = self.client.post(_remove_async_tag_url(),
                                    data={'name': 'colorless'},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        eq_(response.status_code, 200)
        eq_([t.name for t in Question.objects.get(pk=2).tags.all()], ['green'])

    def test_remove_async_unapplied_tag(self):
        """Assert trying to remove a tag that isn't there succeeds."""
        response = self.client.post(_remove_async_tag_url(),
                                    data={'name': 'lemon'},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        eq_(response.status_code, 200)

    def test_remove_async_no_tag(self):
        """Assert calling the remove handler with no param fails."""
        response = self.client.post(_remove_async_tag_url(),
                                    data={},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertContains(response, NO_TAG, status_code=400)


class TaggingViewTestsAsAdmin(TaggingTestCaseBase):
    """Tests for views that create new tags, logged in as someone who can"""

    def setUp(self):
        super(TaggingViewTestsAsAdmin, self).setUp()
        self.client.login(username='admin', password='testpass')

    def tearDown(self):
        self.client.logout()
        super(TaggingViewTestsAsAdmin, self).tearDown()

    def test_add_new_tag(self):
        """Assert adding a nonexistent tag sychronously creates & adds it."""
        self.client.post(_add_tag_url(), data={'tag-name': 'nonexistent tag'})
        tags_eq(Question.objects.get(pk=1), ['nonexistent tag'])

    def test_add_async_new_tag(self):
        """Assert adding an nonexistent tag creates & adds it."""
        response = self.client.post(_add_async_tag_url(),
                                    data={'tag-name': 'nonexistent tag'},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        eq_(response.status_code, 200)
        tags_eq(Question.objects.get(pk=1), ['nonexistent tag'])

    def test_add_new_case_insensitive(self):
        """Adding a tag differing only in case from existing ones shouldn't
        create a new tag."""
        self.client.post(_add_async_tag_url(), data={'tag-name': 'RED'},
                         HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        tags_eq(Question.objects.get(pk=1), ['red'])

    def test_add_new_canonicalizes(self):
        """Adding a new tag as an admin should still canonicalize case."""
        response = self.client.post(_add_async_tag_url(),
                                    data={'tag-name': 'RED'},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        eq_(json.loads(response.content)['canonicalName'], 'red')


def _add_tag_url():
    """Return the URL to add_tag for question 1, an untagged question."""
    return reverse('questions.add_tag', kwargs={'question_id': 1})


def _add_async_tag_url():
    """Return the URL to add_tag_async for question 1, an untagged question."""
    return reverse('questions.add_tag_async', kwargs={'question_id': 1})


def _remove_tag_url():
    """Return  URL to remove_tag for question 2, tagged {colorless, green}."""
    return reverse('questions.remove_tag', kwargs={'question_id': 2})


def _remove_async_tag_url():
    """Return URL to remove_tag_async on q. 2, tagged {colorless, green}."""
    return reverse('questions.remove_tag_async', kwargs={'question_id': 2})


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
        eq_(4, len(doc('ol.questions li')))

        # solve one question then verify that it doesn't show up
        answer = Answer.objects.all()[0]
        answer.question.solution = answer
        answer.question.save()
        response = self.client.get(url_)
        doc = pq(response.content)
        eq_(3, len(doc('ol.questions li')))
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
        self._my_contributions_test_helper('jsocol', 3)

        # pcraciunoiu should have 2 questions in his contributions'
        self._my_contributions_test_helper('pcraciunoiu', 3)

        # rrosario should have 0 questions in his contributions
        self._my_contributions_test_helper('rrosario', 0)

    def test_contributed_badge(self):
        # pcraciunoiu should have a contributor badge on question 1 but not 2
        self.client.login(username='pcraciunoiu', password="testpass")
        response = get(self.client, 'questions.questions')
        doc = pq(response.content)
        eq_(1, len(doc('li#question-1 span.contributed')))
        eq_(0, len(doc('li#question-2 span.contributed')))

    def test_sort(self):
        default = reverse('questions.questions')
        sorted = urlparams(default, sort='requested')

        q = Question.objects.get(pk=2)
        qv = QuestionVote(question=q, anonymous_id='abc123')
        qv.save()

        response = self.client.get(default)
        doc = pq(response.content)
        eq_('question-1', doc('ol.questions li')[0].attrib['id'])

        response = self.client.get(sorted)
        doc = pq(response.content)
        eq_('question-2', doc('ol.questions li')[0].attrib['id'])

    def test_top_contributors(self):
        # There should be no top contributors since there are no solutions.
        cache_top_contributors()
        response = get(self.client, 'questions.questions')
        doc = pq(response.content)
        eq_(0, len(doc('#top-contributors ol li')))

        # Solve a question and verify we now have a top conributor.
        answer = Answer.objects.all()[0]
        answer.created = datetime.now()
        answer.save()
        answer.question.solution = answer
        answer.question.save()
        cache_top_contributors()
        response = get(self.client, 'questions.questions')
        doc = pq(response.content)
        lis = doc('#top-contributors ol li')
        eq_(1, len(lis))
        eq_('pcraciunoiu', lis[0].text)

        # Make answer 8 days old. There should no be top contributors.
        answer.created = datetime.now() - timedelta(days=8)
        answer.save()
        cache_top_contributors()
        response = get(self.client, 'questions.questions')
        doc = pq(response.content)
        eq_(0, len(doc('#top-contributors ol li')))

    def test_tagged(self):
        self.client.login(username='admin', password="testpass")
        tagname = 'mobile'
        tagged = urlparams(reverse('questions.questions'), tagged=tagname)

        # First there should be no questions tagged 'mobile'
        response = self.client.get(tagged)
        doc = pq(response.content)
        eq_(0, len(doc('ol.questions > li')))

        # Tag a question 'mobile'
        question = Question.objects.get(pk=2)
        response = post(self.client, 'questions.add_tag',
                        {'tag-name': tagname},
                        args=[question.id])
        eq_(200, response.status_code)

        # Now there should be 1 question tagged 'mobile'
        response = self.client.get(tagged)
        doc = pq(response.content)
        eq_(1, len(doc('ol.questions > li')))


class QuestionEditingTests(TestCaseBase):
    """Tests for the question-editing view and templates"""

    def setUp(self):
        super(QuestionEditingTests, self).setUp()
        self.client.login(username='admin', password='testpass')

    def tearDown(self):
        self.client.logout()
        super(QuestionEditingTests, self).tearDown()

    def test_extra_fields(self):
        """The edit-question form should show appropriate metadata fields."""
        question_id = 1
        response = get(self.client, 'questions.edit_question',
                       kwargs={'question_id': question_id})
        eq_(response.status_code, 200)

        # Make sure each extra metadata field is in the form:
        doc = pq(response.content)
        q = Question.objects.get(pk=question_id)
        extra_fields = q.product.get('extra_fields', []) + \
                       q.category.get('extra_fields', [])
        for field in extra_fields:
            assert doc('input[name=%s]' % field) or \
                   doc('textarea[name=%s]' % field), \
                   "The %s field is missing from the edit page.""" % field

    def test_no_extra_fields(self):
        """The edit-question form shouldn't show inappropriate metadata."""
        response = get(self.client, 'questions.edit_question',
                       kwargs={'question_id': 2})
        eq_(response.status_code, 200)

        # Take the "os" field as representative. Make sure it doesn't show up:
        doc = pq(response.content)
        assert not doc('input[name=os]')

    def test_post(self):
        """Posting a valid edit form should save the question."""
        question_id = 1
        response = post(self.client, 'questions.edit_question',
                       {'title': 'New title',
                        'content': 'New content',
                        'ff_version': 'New version'},
                       kwargs={'question_id': question_id})

        # Make sure the form redirects and thus appears to succeed:
        url = 'http://testserver%s' % reverse('questions.answers',
                                           kwargs={'question_id': question_id},
                                           force_locale=True)
        self.assertRedirects(response, url)

        # Make sure the static fields, the metadata, and the updated_by field
        # changed:
        q = Question.objects.get(pk=question_id)
        eq_(q.title, 'New title')
        eq_(q.content, 'New content')
        eq_(q.metadata['ff_version'], 'New version')
        eq_(q.updated_by, User.objects.get(username='admin'))


class AAQTemplateTestCase(TestCaseBase):
    """Test the AAQ template."""
    def setUp(self):
        super(AAQTemplateTestCase, self).setUp()
        self.client.login(username='jsocol', password='testpass')

    def tearDown(self):
        super(AAQTemplateTestCase, self).tearDown()
        self.client.logout()

    def test_full_workflow(self):
        # Post a new question
        url = urlparams(reverse('questions.new_question'),
                        product='desktop', category='d1',
                        search='A test question', showform=1)
        data = {'title': 'A test question',
                'content': 'I have this question that I hope...',
                'sites_affected': 'http://example.com',
                'ff_version': '3.6.6',
                'os': 'Intel Mac OS X 10.6',
                'plugins': '* Shockwave Flash 10.1 r53',
                'useragent': 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X ' +
                             '10.6; en-US; rv:1.9.2.6) Gecko/20100625 ' +
                             'Firefox/3.6.6'}

        response = self.client.post(url, data)
        eq_(200, response.status_code)

        # Verify questions is in db now
        question = Question.objects.filter(title='A test question')[0]
        eq_(UNCONFIRMED, question.status)

        # Verify question doesn't show up in questions list yet
        response = get(self.client, 'questions.questions')
        doc = pq(response.content)
        eq_(0, len(doc('li#question-%s' % question.id)))

        # Confirm the question and make sure it now appears in questions list
        response = post(self.client, 'questions.confirm_form', {},
                        args=[question.id, question.confirmation_id])
        eq_(1, len(response.redirect_chain))
        eq_(('http://testserver/en-US/questions/%s' % question.id, 302),
            response.redirect_chain[0])
        doc = pq(response.content)
        eq_('jsocol', doc('#question div.asked-by span.user').text())
        response = get(self.client, 'questions.questions')
        doc = pq(response.content)
        eq_(1, len(doc('li#question-%s' % question.id)))

    def test_invalid_product_404(self):
        url = urlparams(reverse('questions.new_question'), product='lipsum')
        response = self.client.get(url)
        eq_(404, response.status_code)

    def test_invalid_category_404(self):
        url = urlparams(reverse('questions.new_question'),
                        product='desktop', category='lipsum')
        response = self.client.get(url)
        eq_(404, response.status_code)
