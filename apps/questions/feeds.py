from django.shortcuts import get_object_or_404
from django.utils.html import strip_tags, escape
from django.contrib.syndication.views import Feed
from django.utils.feedgenerator import Atom1Feed

from tower import ugettext as _

from sumo.urlresolvers import reverse
from taggit.models import Tag
from sumo.helpers import urlparams

from .models import Question, CONFIRMED
import questions as constants


class QuestionsFeed(Feed):
    feed_type = Atom1Feed

    def title(self):
        return _('Recently updated questions')

    def link(self):
        return reverse('questions.questions')

    def items(self):
        qs = Question.objects.filter(status=CONFIRMED)
        return qs.order_by('-updated')[:constants.QUESTIONS_PER_PAGE]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return escape(item.content_parsed)

    def item_author_name(self, item):
        return item.creator

    def item_pubdate(self, item):
        return item.created


class TaggedQuestionsFeed(QuestionsFeed):

    def get_object(self, request, tag_slug):
        return get_object_or_404(Tag, slug=tag_slug)

    def title(self, tag):
        return _('Recently updated questions tagged %s' % tag.name)

    def link(self, tag):
        return urlparams(reverse('questions.questions'), tagged=tag.slug)

    def items(self, tag):
        qs = Question.objects.filter(status=CONFIRMED, tags__in=[tag.name])
        return qs.order_by('-updated')[:constants.QUESTIONS_PER_PAGE]


class AnswersFeed(Feed):
    feed_type = Atom1Feed

    def get_object(self, request, question_id):
        return get_object_or_404(Question, pk=question_id)

    def title(self, question):
        return _('Recent answers to %s') % question.title

    def link(self, question):
        return question.get_absolute_url()

    def description(self, question):
        return self.title(question)

    def items(self, question):
        return question.answers.order_by('-created')

    def item_title(self, item):
        return strip_tags(item.content_parsed)[:100]

    def item_description(self, item):
        return escape(item.content_parsed)

    def item_author_name(self, item):
        return item.creator

    def item_pubdate(self, item):
        return item.created
