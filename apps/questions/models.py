from django.db import models
from django.contrib.auth.models import User

from sumo.models import ModelBase


class QuestionForum(ModelBase):
    """A collection of questions."""
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True)

    def __unicode__(self):
        return self.name


class Question(ModelBase):
    """A support question."""
    title = models.CharField(max_length=255)
    forum = models.ForeignKey('QuestionForum', related_name='questions')
    creator = models.ForeignKey(User, related_name='questions')
    content = models.TextField()
    created = models.DateTimeField(auto_now_add=True, db_index=True)
    updated = models.DateTimeField(null=True, db_index=True)
    updated_by = models.ForeignKey(User, null=True, related_name='questions_updated')
    last_answer = models.ForeignKey('Answer', related_name='last_reply_in',
                                    null=True)
    num_answers = models.IntegerField(default=0, db_index=True)
    status = models.IntegerField(db_index=True)
    is_locked = models.BooleanField(default=False)

    class Meta:
        ordering = ['-last_answer__created', '-created']

    def __unicode__(self):
        return self.title


class QuestionMetaData(ModelBase):
    """Metadata associated with a support question."""
    question = models.ForeignKey('Question', related_name='meta_data')
    name = models.SlugField(db_index=True)
    value = models.TextField()

    def __unicode__(self):
        return u'%s: %s' % (self.name, self.value[:50])


class Answer(ModelBase):
    """An answer to a support question."""
    question = models.ForeignKey('Question', related_name='answers')
    creator = models.ForeignKey(User, related_name='answers')
    created = models.DateTimeField(auto_now_add=True, db_index=True)
    content = models.TextField()
    updated = models.DateTimeField(null=True, db_index=True)
    updated_by = models.ForeignKey(User, null=True,
                                   related_name='answers_updated')
    upvotes = models.IntegerField(default=0, db_index=True)

    def __unicode__(self):
        return u'%s: %s' % (self.question.title, self.content[:50])
