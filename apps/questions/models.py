from datetime import datetime, timedelta
import re
import random
import string

from django.db import models
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic

import product_details
from taggit.models import Tag

from flagit.models import FlaggedObject
from notifications import create_watch
from notifications.tasks import delete_watches
from sumo.models import ModelBase, TaggableMixin
from sumo.urlresolvers import reverse
from sumo.utils import wiki_to_html
from sumo.helpers import urlparams
import questions as constants
from questions.tags import add_existing_tag
from .question_config import products
from .tasks import (update_question_votes, build_answer_notification,
                    update_answer_pages)
from upload.models import ImageAttachment


UNCONFIRMED = 0
CONFIRMED = 1
QUESTION_STATUS_CHOICES = (
    (UNCONFIRMED, 'Unconfirmed'),
    (CONFIRMED, 'Confirmed'),
)


class Question(ModelBase, TaggableMixin):
    """A support question."""
    title = models.CharField(max_length=255)
    creator = models.ForeignKey(User, related_name='questions')
    content = models.TextField()

    created = models.DateTimeField(default=datetime.now, db_index=True)
    updated = models.DateTimeField(default=datetime.now, db_index=True)
    updated_by = models.ForeignKey(User, null=True,
                                   related_name='questions_updated')
    last_answer = models.ForeignKey('Answer', related_name='last_reply_in',
                                    null=True)
    num_answers = models.IntegerField(default=0, db_index=True)
    solution = models.ForeignKey('Answer', related_name='solution_for',
                                 null=True)
    status = models.IntegerField(default=UNCONFIRMED, db_index=True,
                                 choices=QUESTION_STATUS_CHOICES)
    is_locked = models.BooleanField(default=False)
    num_votes_past_week = models.PositiveIntegerField(default=0, db_index=True)
    confirmation_id = models.CharField(max_length=40, db_index=True)

    images = generic.GenericRelation(ImageAttachment)
    flags = generic.GenericRelation(FlaggedObject)

    class Meta:
        ordering = ['-updated']
        permissions = (
                ('tag_question',
                 'Can add tags to and remove tags from questions'),
            )

    def __unicode__(self):
        return self.title

    @property
    def content_parsed(self):
        return wiki_to_html(self.content)

    def save(self, no_update=False, *args, **kwargs):
        """Override save method to take care of updated."""
        new = not self.id

        if not new and not no_update:
            self.updated = datetime.now()

        # Generate a confirmation_id if necessary
        if new and not self.confirmation_id:
            chars = [random.choice(string.ascii_letters) for x in xrange(10)]
            self.confirmation_id = "".join(chars)

        super(Question, self).save(*args, **kwargs)

        if new:
            # Authors should automatically watch their own questions.
            create_watch(Question, self.id, self.creator.email, 'reply')

    def delete(self, *args, **kwargs):
        """Override delete to trigger delete_watches."""
        delete_watches.delay(Question, self.pk)
        super(Question, self).delete(*args, **kwargs)

    def add_metadata(self, **kwargs):
        """Add (save to db) the passed in metadata.

        Usage:
        question = Question.objects.get(pk=1)
        question.add_metadata(ff_version='3.6.3', os='Linux')

        """
        for key, value in kwargs.items():
            QuestionMetaData.objects.create(question=self, name=key,
                                            value=value)
        self._metadata = None

    def clear_mutable_metadata(self):
        """Clear the mutable metadata.

        This excludes immutable fields: user agent, product, and category.

        """
        self.metadata_set.exclude(name__in=['useragent', 'product',
                                            'category']).delete()
        self._metadata = None

    @property
    def metadata(self):
        """Dictionary access to metadata

        Caches the full metadata dict after first call.

        """
        if not hasattr(self, '_metadata') or self._metadata is None:
            self._metadata = dict((m.name, m.value) for
                                  m in self.metadata_set.all())
        return self._metadata

    @property
    def product(self):
        """Return the product this question is about or an empty mapping if
        unknown."""
        md = self.metadata
        if 'product' in md:
            return products.get(md['product'], {})
        return {}

    @property
    def category(self):
        """Return the category this question refers to or an empty mapping if
        unknown."""
        md = self.metadata
        if self.product and 'category' in md:
            return self.product['categories'].get(md['category'], {})
        return {}

    def auto_tag(self):
        """Apply tags to myself that are implied by my metadata.

        You don't need to call save on the question after this.

        """
        to_add = self.product.get('tags', []) + self.category.get('tags', [])

        version = self.metadata.get('ff_version', '')
        if version in product_details.firefox_history_development_releases or \
           version in product_details.firefox_history_stability_releases or \
           version in product_details.firefox_history_major_releases:
            to_add.append('Firefox %s' % version)
            tenths = _tenths_version(version)
            if tenths:
                to_add.append('Firefox %s' % tenths)

        self.tags.add(*to_add)

        # Add a tag for the OS if it already exists as a tag:
        os = self.metadata.get('os')
        if os:
            try:
                add_existing_tag(os, self.tags)
            except Tag.DoesNotExist:
                pass

    def get_absolute_url(self):
        return reverse('questions.answers',
                       kwargs={'question_id': self.id})

    @property
    def num_votes(self):
        """Get the number of votes for this question."""
        return QuestionVote.objects.filter(question=self).count()

    def sync_num_votes_past_week(self):
        """Get the number of votes for this question in the past week."""
        last_week = datetime.now().date() - timedelta(days=7)
        n = QuestionVote.objects.filter(question=self,
                                        created__gte=last_week).count()
        self.num_votes_past_week = n
        return n

    def has_voted(self, request):
        """Did the user already vote?"""
        if request.user.is_authenticated():
            qs = QuestionVote.objects.filter(question=self,
                                             creator=request.user)
        elif request.anonymous.has_id:
            anon_id = request.anonymous.anonymous_id
            qs = QuestionVote.objects.filter(question=self,
                                             anonymous_id=anon_id)
        else:
            return False

        return qs.count() > 0

    @property
    def helpful_replies(self):
        """Return answers that have been voted as helpful."""
        votes = AnswerVote.objects.filter(answer__question=self, helpful=True)
        helpful_ids = list(votes.values_list('answer', flat=True).distinct())
        # Exclude the solution if it is set
        if self.solution and self.solution.id in helpful_ids:
            helpful_ids.remove(self.solution.id)

        if len(helpful_ids) > 0:
            return self.answers.filter(id__in=helpful_ids)
        else:
            return []

    def is_contributor(self, user):
        """Did the passed in user contribute to this question?"""
        if user.is_authenticated():
            qs = self.answers.filter(creator=user)
            if self.creator == user or qs.count() > 0:
                return True

        return False


class QuestionMetaData(ModelBase):
    """Metadata associated with a support question."""
    question = models.ForeignKey('Question', related_name='metadata_set')
    name = models.SlugField(db_index=True)
    value = models.TextField()

    class Meta:
        unique_together = ('question', 'name')

    def __unicode__(self):
        return u'%s: %s' % (self.name, self.value[:50])


class Answer(ModelBase):
    """An answer to a support question."""
    question = models.ForeignKey('Question', related_name='answers')
    creator = models.ForeignKey(User, related_name='answers')
    created = models.DateTimeField(default=datetime.now, db_index=True)
    content = models.TextField()
    updated = models.DateTimeField(default=datetime.now, db_index=True)
    updated_by = models.ForeignKey(User, null=True,
                                   related_name='answers_updated')
    upvotes = models.IntegerField(default=0, db_index=True)
    page = models.IntegerField(default=1)

    images = generic.GenericRelation(ImageAttachment)
    flags = generic.GenericRelation(FlaggedObject)

    class Meta:
        ordering = ['created']

    def __unicode__(self):
        return u'%s: %s' % (self.question.title, self.content[:50])

    @property
    def content_parsed(self):
        return wiki_to_html(self.content)

    def save(self, no_update=False, no_notify=False, *args, **kwargs):
        """
        Override save method to update question info and take care of
        updated.
        """

        new = self.id is None

        if new:
            page = self.question.num_answers / constants.ANSWERS_PER_PAGE + 1
            self.page = page
        else:
            self.updated = datetime.now()

        super(Answer, self).save(*args, **kwargs)

        if new:
            self.question.num_answers = self.question.answers.count()
            self.question.last_answer = self
            self.question.save(no_update)

            if not no_notify:
                build_answer_notification.delay(self)

    def delete(self, *args, **kwargs):
        """Override delete method to update parent question info."""
        question = Question.uncached.get(pk=self.question.id)
        if question.last_answer == self:
            answers = question.answers.all().order_by('-created')
            try:
                question.last_answer = answers[1]
            except IndexError:
                # The question has only one answer
                question.last_answer = None
        if question.solution == self:
            question.solution = None

        question.num_answers = question.answers.count() - 1
        question.save()

        super(Answer, self).delete(*args, **kwargs)

        update_answer_pages.delay(question)

    def get_absolute_url(self):
        query = {}
        if self.page > 1:
            query = {'page': self.page}

        url = reverse('questions.answers',
                      kwargs={'question_id': self.question_id})
        return urlparams(url, hash='answer-%s' % self.id, **query)

    @property
    def num_votes(self):
        """Get the total number of votes for this answer."""
        return AnswerVote.objects.filter(answer=self).count()

    @property
    def creator_num_posts(self):
        criteria = models.Q(answers__creator=self.creator) |\
                   models.Q(creator=self.creator)
        return Question.objects.filter(criteria).count()

    @property
    def creator_num_answers(self):
        return Question.objects.filter(
                    solution__in=Answer.objects.filter(
                                    creator=self.creator)).count()

    @property
    def num_helpful_votes(self):
        """Get the number of helpful votes for this answer."""
        return AnswerVote.objects.filter(answer=self, helpful=True).count()

    def has_voted(self, request):
        """Did the user already vote for this answer?"""
        if request.user.is_authenticated():
            qs = AnswerVote.objects.filter(answer=self,
                                           creator=request.user)
        elif request.anonymous.has_id:
            anon_id = request.anonymous.anonymous_id
            qs = AnswerVote.objects.filter(answer=self,
                                           anonymous_id=anon_id)
        else:
            return False

        return qs.count() > 0


class QuestionVote(ModelBase):
    """I have this problem too.
    Keeps track of users that have problem over time."""
    question = models.ForeignKey('Question', related_name='votes')
    created = models.DateTimeField(default=datetime.now, db_index=True)
    creator = models.ForeignKey(User, related_name='question_votes',
                                null=True)
    anonymous_id = models.CharField(max_length=40, db_index=True)


class AnswerVote(ModelBase):
    """Helpful or Not Helpful vote on Answer."""
    answer = models.ForeignKey('Answer', related_name='votes')
    helpful = models.BooleanField(default=False)
    created = models.DateTimeField(default=datetime.now, db_index=True)
    creator = models.ForeignKey(User, related_name='answer_votes',
                                null=True)
    anonymous_id = models.CharField(max_length=40, db_index=True)


def send_vote_update_task(**kwargs):
    if kwargs.get('created'):
        q = kwargs.get('instance').question
        update_question_votes.delay(q)

post_save.connect(send_vote_update_task, sender=QuestionVote)


_tenths_version_pattern = re.compile(r'(\d+\.\d+).*')


def _tenths_version(full_version):
    """Return the major and minor version numbers from a full version string.

    Don't return bugfix version, beta status, or anything futher. If there is
    no major or minor version in the string, return ''.

    """
    match = _tenths_version_pattern.match(full_version)
    if match:
        return match.group(1)
    return ''
