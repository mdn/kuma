from django.db import models
from django.contrib.auth.models import User

from sumo.models import ModelBase


class QuestionForum(ModelBase):
    """A collection of questions."""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True)

    def __unicode__(self):
        return self.name


class Question(ModelBase):
    """A support question."""
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    forum = models.ForeignKey('QuestionForum')
    creator = models.ForeignKey(User)
    content = models.TextField()
    created = models.DateTimeField(auto_now_add=True, db_index=True)
    updated = models.DateTimeField(null=True, db_index=True)
    updated_by = models.ForeignKey(User, null=True)
    last_answer = models.ForeignKey('Answer', related_name='last_reply_in',
                                    null=True)
    answers = models.IntegerField(default=0, db_index=True)
    status = models.IntegerField(db_index=True)
    is_locked = models.BooleanField(default=False)

    class Meta:
        ordering = ['-last_answer__created', '-created']

    def __unicode__(self):
        return self.title


class QuestionMetaData(ModelBase):
    """Metadata associated with a support question."""
    id = models.AutoField(primary_key=True)
    question = models.ForeignKey('Question')
    name = models.SlugField(db_index=True)
    value = models.TextField()

    def __unicode__(self):
        return u'%s: %s' % (self.name, self.value[:50])


class Answer(ModelBase):
    """An answer to a support question."""
    id = models.AutoField(primary_key=True)
    question = models.ForeignKey('Question')
    creator = models.ForeignKey(User)
    created = models.DateTimeField(auto_now_add=True, db_index=True)
    content = models.TextField()
    updated = models.DateTimeField(null=True, db_index=True)
    updated_by = models.ForeignKey(User, null=True)
    upvotes = models.IntegerField(default=0, db_index=True)

    def __unicode__(self):
        return u'%s: %s' % (self.question.title, self.content[:50])
