from datetime import datetime, timedelta

from django.db import models
from django.contrib.auth.models import User

import jinja2

from sumo.models import ModelBase
from sumo.utils import WikiParser
from sumo.urlresolvers import reverse
from sumo.helpers import urlparams
import questions as constants


class Question(ModelBase):
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
    status = models.IntegerField(default=0, db_index=True)
    is_locked = models.BooleanField(default=False)

    class Meta:
        ordering = ['-updated']

    def __unicode__(self):
        return self.title

    @property
    def content_parsed(self):
        parser = WikiParser()
        return jinja2.Markup(parser.parse(self.content, False))

    def save(self, *args, **kwargs):
        """Override save method to take care of updated."""
        if self.id:
            self.updated = datetime.now()
        super(Question, self).save(*args, **kwargs)

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

    @property
    def metadata(self):
        """Dictionary access to metadata.
        Caches the full metadata dict after first call."""
        if not hasattr(self, '_metadata') or self._metadata == None:
            self._metadata = {}
            for metadata in self.metadata_set.all():
                self._metadata[metadata.name] = metadata.value

        return self._metadata

    def get_absolute_url(self):
        return reverse('questions.answers',
                       kwargs={'question_id': self.id})

    @property
    def num_votes(self):
        """Get the number of votes for this question."""
        return QuestionVote.objects.filter(question=self).count()

    @property
    def num_votes_past_week(self):
        """Get the number of votes for this question in the past week."""
        last_week = datetime.now().date() - timedelta(days=7)
        return QuestionVote.objects.filter(question=self,
                                           created__gte=last_week).count()

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


class QuestionMetaData(ModelBase):
    """Metadata associated with a support question."""
    question = models.ForeignKey('Question', related_name='metadata_set')
    name = models.SlugField(db_index=True)
    value = models.TextField()

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

    class Meta:
        ordering = ['created']

    def __unicode__(self):
        return u'%s: %s' % (self.question.title, self.content[:50])

    @property
    def content_parsed(self):
        parser = WikiParser()
        return jinja2.Markup(parser.parse(self.content, False))

    def save(self, *args, **kwargs):
        """Override save method to update question info and take care of
        updated.
        """

        new = self.id is None

        if not new:
            self.updated = datetime.now()

        super(Answer, self).save(*args, **kwargs)

        if new:
            self.question.num_answers = self.question.answers.count()
            self.question.last_answer = self
            self.question.save()

            # TODO: Send notifications to thread watchers.
            #build_notification.delay(self)

    @property
    def page(self):
        """Get the page of the question on which this answer is found."""
        t = self.question
        earlier = t.answers.filter(created__lte=self.created).count() - 1
        if earlier < 1:
            return 1
        return earlier / constants.ANSWERS_PER_PAGE + 1

    def get_absolute_url(self):
        query = {}
        if self.page > 1:
            query = {'page': self.page}

        url = self.question.get_absolute_url()
        return urlparams(url, hash='answer-%s' % self.id, **query)


class QuestionVote(ModelBase):
    """I have this problem too.
    Keeps track of users that have problem over time."""
    question = models.ForeignKey('Question', related_name='votes')
    created = models.DateTimeField(default=datetime.now, db_index=True)
    creator = models.ForeignKey(User, related_name='question_votes',
                                null=True)
    anonymous_id = models.CharField(max_length=40, db_index=True)
