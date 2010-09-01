from django.contrib.auth.models import User

from nose.tools import eq_, raises

from notifications import check_watch
import sumo.models
from taggit.models import Tag

from flagit.models import FlaggedObject
from questions.models import (Question, QuestionMetaData, Answer,
                              _tenths_version)
from questions.tags import add_existing_tag
from questions.tasks import update_answer_pages
from questions.tests import TestCaseBase, TaggingTestCaseBase, tags_eq
from questions.question_config import products


class TestAnswer(TestCaseBase):
    """Test the Answer model"""

    def test_new_answer_updates_question(self):
        """Test saving a new answer updates the corresponding question.
        Specifically, last_post and num_replies should update."""
        question = Question(title='Test Question',
                            content='Lorem Ipsum Dolor',
                            creator_id=118533)
        question.save()

        eq_(0, question.num_answers)
        eq_(None, question.last_answer)

        answer = Answer(question=question, creator_id=47963,
                        content="Test Answer")
        answer.save()

        question = Question.objects.get(pk=question.id)
        eq_(1, question.num_answers)
        eq_(answer, question.last_answer)

        question.delete()

    def test_delete_question_removes_flag(self):
        """Deleting a question also removes the flags on that question."""
        question = Question(title='Test Question',
                            content='Lorem Ipsum Dolor',
                            creator_id=118533)
        question.save()
        FlaggedObject.objects.create(
            status=0, content_object=question,
            reason='language', creator_id=118533)
        eq_(1, FlaggedObject.objects.count())

        question.delete()
        eq_(0, FlaggedObject.objects.count())

    def test_delete_answer_removes_flag(self):
        """Deleting an answer also removes the flags on that answer."""
        question = Question(title='Test Question',
                            content='Lorem Ipsum Dolor',
                            creator_id=118533)
        question.save()

        answer = Answer(question=question, creator_id=47963,
                        content="Test Answer")
        answer.save()

        FlaggedObject.objects.create(
            status=0, content_object=answer,
            reason='language', creator_id=118533)
        eq_(1, FlaggedObject.objects.count())

        answer.delete()
        eq_(0, FlaggedObject.objects.count())

    def test_delete_last_answer_of_question(self):
        """Deleting the last_answer of a Question should update the question.
        """
        question = Question.objects.get(pk=1)
        last_answer = question.last_answer

        # add a new answer and verify last_answer updated
        answer = Answer(question=question, creator_id=47963,
                        content="Test Answer")
        answer.save()
        question = Question.objects.get(pk=question.id)

        eq_(question.last_answer.id, answer.id)

        # delete the answer and last_answer should go back to previous value
        answer.delete()
        question = Question.objects.get(pk=question.id)
        eq_(question.last_answer.id, last_answer.id)
        eq_(Answer.objects.filter(pk=answer.id).count(), 0)

    def test_delete_solution_of_question(self):
        """Deleting the solution of a Question should update the question.
        """
        # set a solution to the question
        question = Question.objects.get(pk=1)
        solution = question.last_answer
        question.solution = solution
        question.save()

        # delete the solution and question.solution should go back to None
        solution.delete()
        question = Question.objects.get(pk=question.id)
        eq_(question.solution, None)

    def test_update_page_task(self):
        answer = Answer.objects.get(pk=1)
        answer.page = 4
        answer.save()
        answer = Answer.objects.get(pk=1)
        assert answer.page == 4
        update_answer_pages(answer.question)
        a = Answer.objects.get(pk=1)
        assert a.page == 1

    def test_delete_updates_pages(self):
        a1 = Answer.objects.get(pk=2)
        a2 = Answer.objects.get(pk=3)
        a1.page = 7
        a1.save()
        a2.delete()
        a3 = Answer.objects.filter(question=a1.question)[0]
        assert a3.page == 1, "Page was %s" % a3.page

    def test_creator_num_posts(self):
        """Test retrieval of post count for creator of a particular answer"""
        question = Question.objects.all()[0]
        answer = Answer(question=question, creator_id=47963,
                        content="Test Answer")

        eq_(answer.creator_num_posts, 4)

    def test_creator_num_answers(self):
        """Test retrieval of answer count for creator of a particular answer"""
        question = Question.objects.all()[0]
        answer = Answer(question=question, creator_id=47963,
                        content="Test Answer")
        answer.save()

        question.solution = answer
        question.save()

        eq_(answer.creator_num_answers, 1)


class TestQuestionMetadata(TestCaseBase):
    """Tests handling question metadata"""

    def setUp(self):
        super(TestQuestionMetadata, self).setUp()

        # add a new Question to test with
        question = Question(title='Test Question',
                            content='Lorem Ipsum Dolor',
                            creator_id=1)
        question.save()
        self.question = question

    def tearDown(self):
        super(TestQuestionMetadata, self).tearDown()

        # remove the added Question
        self.question.delete()

    def test_add_metadata(self):
        """Test the saving of metadata."""
        metadata = {'version': u'3.6.3', 'os': u'Windows 7'}
        self.question.add_metadata(**metadata)
        saved = QuestionMetaData.objects.filter(question=self.question)
        eq_(dict((x.name, x.value) for x in saved), metadata)

    def test_metadata_property(self):
        """Test the metadata property on Question model."""
        self.question.add_metadata(crash_id='1234567890')
        eq_('1234567890', self.question.metadata['crash_id'])

    def test_product_property(self):
        """Test question.product property."""
        self.question.add_metadata(product='desktop')
        eq_(products['desktop'], self.question.product)

    def test_category_property(self):
        """Test question.category property."""
        self.question.add_metadata(product='desktop')
        self.question.add_metadata(category='d1')
        eq_(products['desktop']['categories']['d1'], self.question.category)

    def test_clear_mutable_metadata(self):
        """Make sure it works and clears the internal cache.

        crash_id should get cleared, while product, category, and useragent
        should remain.

        """
        q = self.question
        q.add_metadata(product='desktop', category='d1', useragent='Fyerfocks',
                       crash_id='7')

        q.metadata
        q.clear_mutable_metadata()
        md = q.metadata
        assert 'crash_id' not in md, \
            "clear_mutable_metadata() didn't clear the cached metadata."
        eq_(dict(product='desktop', category='d1', useragent='Fyerfocks'), md)

    def test_auto_tagging(self):
        """Make sure tags get applied based on metadata on first save."""
        Tag.objects.create(slug='green', name='green')
        q = self.question
        q.add_metadata(product='desktop', category='d1', ff_version='3.6.8',
                       os='GREen')
        q.save()
        q.auto_tag()
        tags_eq(q, ['desktop', 'websites', 'Firefox 3.6.8', 'Firefox 3.6',
                    'green'])

    def test_auto_tagging_restraint(self):
        """Auto-tagging shouldn't tag unknown Firefox versions or OSes."""
        q = self.question
        q.add_metadata(ff_version='allyourbase', os='toaster 1.0')
        q.save()
        q.auto_tag()
        tags_eq(q, [])

    def test_tenths_version(self):
        """Test the filter that turns 1.2.3 into 1.2."""
        eq_(_tenths_version('1.2.3beta3'), '1.2')
        eq_(_tenths_version('1.2rc'), '1.2')
        eq_(_tenths_version('1.w'), '')


class QuestionTests(TestCaseBase):
    """Tests for Question model"""

    def test_save_updated(self):
        """Make sure saving updates the `updated` field."""
        q = Question.objects.all()[0]
        updated = q.updated
        q.save()
        self.assertNotEqual(updated, q.updated)

    def test_save_no_update(self):
        """Saving with the `no_update` option shouldn't update `updated`."""
        q = Question.objects.all()[0]
        updated = q.updated
        q.save(no_update=True)
        eq_(updated, q.updated)

    def test_default_manager(self):
        """Assert Question's default manager is SUMO's ManagerBase.

        This is easy to get wrong when mixing in taggability.

        """
        eq_(Question._default_manager.__class__, sumo.models.ManagerBase)

    def test_notification_created(self):
        """Creating a new question auto-watches it."""

        u = User.objects.get(pk=118533)
        q = Question(creator=u, title='foo', content='bar')
        q.save()

        assert check_watch(Question, q.id, u.email, 'reply')

    def test_no_notification_on_update(self):
        """Saving an existing question does not watch it."""

        q = Question.objects.get(pk=1)
        assert not check_watch(Question, q.id, q.creator.email, 'reply')

        q.save()
        assert not check_watch(Question, q.id, q.creator.email, 'reply')


class AddExistingTagTests(TaggingTestCaseBase):
    """Tests for the add_existing_tag helper function."""

    def setUp(self):
        super(AddExistingTagTests, self).setUp()
        self.untagged_question = Question.objects.get(pk=1)

    def test_tags_manager(self):
        """Make sure the TaggableManager exists.

        Full testing of functionality is a matter for taggit's tests.

        """
        tags_eq(self.untagged_question, [])

    def test_add_existing_case_insensitive(self):
        """Assert add_existing_tag works case-insensitively."""
        add_existing_tag('LEMON', self.untagged_question.tags)
        tags_eq(self.untagged_question, [u'lemon'])

    @raises(Tag.DoesNotExist)
    def test_add_existing_no_such_tag(self):
        """Assert add_existing_tag doesn't work when the tag doesn't exist."""
        add_existing_tag('nonexistent tag', self.untagged_question.tags)
