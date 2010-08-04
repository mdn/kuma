from django.shortcuts import get_object_or_404
from django.utils.html import strip_tags, escape
from django.contrib.syndication.views import Feed
from django.utils.feedgenerator import Atom1Feed
from django.utils.encoding import smart_str

from tower import ugettext as _

from sumo.urlresolvers import reverse

from .models import Question
import questions as constants


class QuestionsFeed(Feed):
    feed_type = Atom1Feed

    def title(self):
        return _('Recently updated questions')

    def link(self):
        return reverse('questions.questions')

    def items(self):
        return Question.objects.all().order_by(
            '-updated')[:constants.QUESTIONS_PER_PAGE]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return escape(item.content_parsed)

    def item_author_name(self, item):
        return item.creator

    def item_pubdate(self, item):
        return item.created


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
