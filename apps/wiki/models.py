import logging
from collections import namedtuple
from datetime import datetime, timedelta
from itertools import chain
from urlparse import urlparse
import hashlib
import re
import time
import json

from pyquery import PyQuery
from tower import ugettext_lazy as _lazy, ugettext as _
import bleach
import jingo

from django.conf import settings
from django.contrib.auth.models import User
from django.core import serializers
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.urlresolvers import resolve
from django.db import models, transaction
from django.http import Http404
from django.utils.html import strip_tags

from south.modelsinspector import add_introspection_rules
import constance.config
from elasticutils.contrib.django import Indexable

from tidings.models import NotificationsMixin
from search.index import SearchMappingType, register_mapping_type
from search.tasks import register_live_index
from sumo import ProgrammingError
from sumo_locales import LOCALES
from sumo.models import LocaleField
from sumo.urlresolvers import reverse, split_path

from taggit.models import ItemBase, TagBase
from taggit.managers import TaggableManager
from taggit.utils import parse_tags, edit_string_for_tags

from teamwork.models import Team

import waffle

import wiki.content
from wiki import TEMPLATE_TITLE_PREFIX
from wiki.signals import render_done

from . import kumascript

ALLOWED_TAGS = bleach.ALLOWED_TAGS + [
    'div', 'span', 'p', 'br', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'pre', 'code', 'cite',
    'dl', 'dt', 'dd', 'small', 'sub', 'sup', 'u', 'strike', 'samp',
    'ul', 'ol', 'li',
    'nobr', 'dfn', 'caption', 'var', 's',
    'i', 'img', 'hr',
    'input', 'label', 'select', 'option', 'textarea',
    # Note: <iframe> is allowed, but src="" is pre-filtered before bleach
    'iframe',
    'table', 'tbody', 'thead', 'tfoot', 'tr', 'th', 'td', 'colgroup', 'col',
    'section', 'header', 'footer', 'nav', 'article', 'aside', 'figure',
    'figcaption',
    'dialog', 'hgroup', 'mark', 'time', 'meter', 'command', 'output',
    'progress', 'audio', 'video', 'details', 'datagrid', 'datalist', 'table',
    'address', 'font',
    'bdi', 'bdo', 'del', 'ins', 'kbd', 'samp', 'var',
    'ruby', 'rp', 'rt', 'q',
    # MathML
    'math', 'maction', 'menclose', 'merror', 'mfenced', 'mfrac', 'mglyph',
    'mi', 'mlabeledtr', 'mmultiscripts', 'mn', 'mo', 'mover', 'mpadded',
    'mphantom', 'mroot', 'mrow', 'ms', 'mspace', 'msqrt', 'mstyle',
    'msub', 'msup', 'msubsup', 'mtable', 'mtd', 'mtext', 'mtr', 'munder',
    'munderover', 'none', 'mprescripts',
]
ALLOWED_ATTRIBUTES = bleach.ALLOWED_ATTRIBUTES
# Note: <iframe> is allowed, but src="" is pre-filtered before bleach
ALLOWED_ATTRIBUTES['iframe'] = ['id', 'src', 'sandbox', 'seamless',
                                'frameborder', 'width', 'height']
ALLOWED_ATTRIBUTES['p'] = ['style', 'class', 'id', 'align', 'lang', 'dir']
ALLOWED_ATTRIBUTES['span'] = ['style', 'class', 'id', 'title', 'lang', 'dir']
ALLOWED_ATTRIBUTES['img'] = ['src', 'id', 'align', 'alt', 'class', 'is',
                             'title', 'style', 'lang', 'dir', 'width',
                             'height']
ALLOWED_ATTRIBUTES['a'] = ['style', 'id', 'class', 'href', 'title',
                           'lang', 'name', 'dir', 'hreflang', 'rel']
ALLOWED_ATTRIBUTES['i'] = ['class']
ALLOWED_ATTRIBUTES['td'] = ['style', 'id', 'class', 'colspan', 'rowspan',
                            'lang', 'dir']
ALLOWED_ATTRIBUTES['th'] = ['style', 'id', 'class', 'colspan', 'rowspan',
                            'scope', 'lang', 'dir']
ALLOWED_ATTRIBUTES['video'] = ['style', 'id', 'class', 'lang', 'src',
                               'controls', 'dir']
ALLOWED_ATTRIBUTES['font'] = ['color', 'face', 'size', 'dir']
ALLOWED_ATTRIBUTES['select'] = ['name', 'dir']
ALLOWED_ATTRIBUTES['option'] = ['value', 'selected', 'dir']
ALLOWED_ATTRIBUTES['ol'] = ['style', 'class', 'id', 'lang', 'start', 'dir']
ALLOWED_ATTRIBUTES.update(dict((x, ['style', 'class', 'id', 'name', 'lang',
                                    'dir'])
                          for x in
                          ('h1', 'h2', 'h3', 'h4', 'h5', 'h6')))
ALLOWED_ATTRIBUTES.update(dict((x, ['style', 'class', 'id', 'lang', 'dir', 'title'])
                               for x in (
    'div', 'pre', 'ul', 'li', 'code', 'dl', 'dt', 'dd',
    'section', 'header', 'footer', 'nav', 'article', 'aside', 'figure',
    'dialog', 'hgroup', 'mark', 'time', 'meter', 'command', 'output',
    'progress', 'audio', 'details', 'datagrid', 'datalist', 'table',
    'tr', 'address', 'col', 's', 'strong'
)))
ALLOWED_ATTRIBUTES.update(dict((x, ['cite']) for x in (
    'blockquote', 'del', 'ins', 'q'
)))
ALLOWED_ATTRIBUTES['time'] += ['datetime']
ALLOWED_ATTRIBUTES['ins'] = ['datetime']
ALLOWED_ATTRIBUTES['del'] = ['datetime']
# MathML
ALLOWED_ATTRIBUTES.update(dict((x, ['href', 'mathbackground', 'mathcolor',
    'id', 'class', 'style']) for x in (
    'math', 'maction', 'menclose', 'merror', 'mfenced', 'mfrac', 'mglyph',
    'mi', 'mlabeledtr', 'mmultiscripts', 'mn', 'mo', 'mover', 'mpadded',
    'mphantom', 'mroot', 'mrow', 'ms', 'mspace', 'msqrt', 'mstyle',
    'msub', 'msup', 'msubsup', 'mtable', 'mtd', 'mtext', 'mtr', 'munder',
    'munderover', 'none', 'mprescripts')))
ALLOWED_ATTRIBUTES['math'] += ['display', 'dir', 'selection', 'notation',
    'close', 'open', 'separators', 'bevelled', 'denomalign', 'linethickness',
    'numalign', 'largeop', 'maxsize', 'minsize', 'movablelimits', 'rspace',
    'separator', 'stretchy', 'symmetric', 'depth', 'lquote', 'rquote', 'align',
    'columnlines', 'frame', 'rowalign', 'rowspacing', 'rowspan', 'columnspan',
    'accent', 'accentunder', 'dir', 'mathsize', 'mathvariant',
    'subscriptshift', 'supscriptshift', 'scriptlevel', 'displaystyle',
    'scriptsizemultiplier', 'scriptminsize']
ALLOWED_ATTRIBUTES['maction'] += ['actiontype', 'selection']
ALLOWED_ATTRIBUTES['menclose'] += ['notation']
ALLOWED_ATTRIBUTES['mfenced'] += ['close', 'open', 'separators']
ALLOWED_ATTRIBUTES['mfrac'] += ['bevelled', 'denomalign', 'linethickness',
    'numalign']
ALLOWED_ATTRIBUTES['mi'] += ['dir', 'mathsize', 'mathvariant']
ALLOWED_ATTRIBUTES['mi'] += ['mathsize', 'mathvariant']
ALLOWED_ATTRIBUTES['mmultiscripts'] += ['subscriptshift', 'superscriptshift']
ALLOWED_ATTRIBUTES['mo'] += ['largeop', 'lspace', 'maxsize', 'minsize',
    'movablelimits', 'rspace', 'separator', 'stretchy', 'symmetric', 'accent',
    'dir', 'mathsize', 'mathvariant']
ALLOWED_ATTRIBUTES['mover'] += ['accent']
ALLOWED_ATTRIBUTES['mpadded'] += ['lspace', 'voffset', 'depth']
ALLOWED_ATTRIBUTES['mrow'] += ['dir']
ALLOWED_ATTRIBUTES['ms'] += ['lquote', 'rquote', 'dir', 'mathsize',
    'mathvariant']
ALLOWED_ATTRIBUTES['mspace'] += ['depth', 'height', 'width']
ALLOWED_ATTRIBUTES['mstyle'] += ['display', 'dir', 'selection', 'notation',
    'close', 'open', 'separators', 'bevelled', 'denomalign', 'linethickness',
    'numalign', 'largeop', 'maxsize', 'minsize', 'movablelimits', 'rspace',
    'separator', 'stretchy', 'symmetric', 'depth', 'lquote', 'rquote', 'align',
    'columnlines', 'frame', 'rowalign', 'rowspacing', 'rowspan', 'columnspan',
    'accent', 'accentunder', 'dir', 'mathsize', 'mathvariant',
    'subscriptshift', 'supscriptshift', 'scriptlevel', 'displaystyle',
    'scriptsizemultiplier',
    'scriptminsize']
ALLOWED_ATTRIBUTES['msub'] += ['subscriptshift']
ALLOWED_ATTRIBUTES['msubsup'] += ['subscriptshift', 'superscriptshift']
ALLOWED_ATTRIBUTES['msup'] += ['superscriptshift']
ALLOWED_ATTRIBUTES['mtable'] += ['align', 'columnalign', 'columnlines',
    'frame', 'rowalign', 'rowspacing', 'rowlines']
ALLOWED_ATTRIBUTES['mtd'] += ['columnalign', 'columnspan', 'rowalign',
    'rowspan']
ALLOWED_ATTRIBUTES['mtext'] += ['dir', 'mathsize', 'mathvariant']
ALLOWED_ATTRIBUTES['mtr'] += ['columnalign', 'rowalign']
ALLOWED_ATTRIBUTES['munder'] += ['accentunder']
ALLOWED_ATTRIBUTES['mundermover'] = ['accent', 'accentunder']
# CSS
ALLOWED_STYLES = [
    'border', 'border-top', 'border-right', 'border-bottom', 'border-left',
    'float', 'overflow', 'min-height', 'vertical-align',
    'white-space', 'color', 'border-radius', '-webkit-border-radius',
    '-moz-border-radius, -o-border-radius',
    'margin', 'margin-left', 'margin-top', 'margin-bottom', 'margin-right',
    'padding', 'padding-left', 'padding-top', 'padding-bottom',
    'padding-right', 'position', 'top', 'height', 'left', 'right',
    'background',  # TODO: Maybe not this one, it can load URLs
    'background-color',
    'font', 'font-size', 'font-weight', 'font-family', 'font-variant',
    'text-align', 'text-transform',
    '-moz-column-width', '-webkit-columns', 'columns', 'width',
    'list-style-type', 'line-height',
    # CSS properties needed for live examples (pending proper solution):
    'backface-visibility', '-moz-backface-visibility',
    '-webkit-backface-visibility', '-o-backface-visibility', 'perspective',
    '-moz-perspective', '-webkit-perspective', '-o-perspective',
    'perspective-origin', '-moz-perspective-origin',
    '-webkit-perspective-origin', '-o-perspective-origin', 'transform',
    '-moz-transform', '-webkit-transform', '-o-transform', 'transform-style',
    '-moz-transform-style', '-webkit-transform-style', '-o-transform-style',
    'columns', '-moz-columns', '-webkit-columns', 'column-rule',
    '-moz-column-rule', '-webkit-column-rule', 'column-width',
    '-moz-column-width', '-webkit-column-width', 'image-rendering',
    '-ms-interpolation-mode', 'position', 'border-style', 'background-clip',
    'border-bottom-right-radius', 'border-bottom-left-radius',
    'border-top-right-radius', 'border-top-left-radius', 'border-bottom-style',
    'border-left-style', 'border-right-style', 'border-top-style',
    'border-bottom-width', 'border-left-width', 'border-right-width',
    'border-top-width', 'vertical-align', 'border-collapse', 'border-width',
    'border-color', 'border-left', 'border-right', 'border-bottom',
    'border-top', 'clip', 'cursor', 'filter', 'float', 'max-width',
    'font-style', 'letter-spacing', 'opacity', 'zoom', 'text-overflow',
    'text-indent', 'text-rendering', 'text-shadow', 'transition', 'transition',
    'transition', 'transition', 'transition-delay', '-moz-transition-delay',
    '-webkit-transition-delay', '-o-transition-delay', 'transition-duration',
    '-moz-transition-duration', '-webkit-transition-duration',
    '-o-transition-duration', 'transition-property',
    '-moz-transition-property', '-webkit-transition-property',
    '-o-transition-property', 'transition-timing-function',
    '-moz-transition-timing-function',  '-webkit-transition-timing-function',
    '-o-transition-timing-function', 'color', 'display', 'position',
    'outline-color', 'outline', 'outline-offset', 'box-shadow',
    '-moz-box-shadow', '-webkit-box-shadow', '-o-box-shadow',
    'linear-gradient', '-moz-linear-gradient', '-webkit-linear-gradient',
    'radial-gradient', '-moz-radial-gradient', '-webkit-radial-gradient',
    'text-decoration-style', '-moz-text-decoration-style', 'text-decoration',
    'direction', 'white-space', 'unicode-bidi', 'word-wrap'
]

# Disruptiveness of edits to translated versions. Numerical magnitude indicate
# the relative severity.
TYPO_SIGNIFICANCE = 10
MEDIUM_SIGNIFICANCE = 20
MAJOR_SIGNIFICANCE = 30
SIGNIFICANCES = (
    (TYPO_SIGNIFICANCE,
     _lazy(u'Minor details like punctuation and spelling errors')),
    (MEDIUM_SIGNIFICANCE,
     _lazy(u"Content changes that don't require immediate translation")),
    (MAJOR_SIGNIFICANCE,
     _lazy(u'Major content changes that will make older translations '
           'inaccurate')),
)

CATEGORIES = (
    (00, _lazy(u'Uncategorized')),
    (10, _lazy(u'Reference')),
)

# Depth of table-of-contents in document display.
TOC_DEPTH_NONE = 0
TOC_DEPTH_ALL = 1
TOC_DEPTH_H2 = 2
TOC_DEPTH_H3 = 3
TOC_DEPTH_H4 = 4

TOC_DEPTH_CHOICES = (
    (TOC_DEPTH_NONE, _lazy(u'No table of contents')),
    (TOC_DEPTH_ALL, _lazy(u'All levels')),
    (TOC_DEPTH_H2, _lazy(u'H2 and higher')),
    (TOC_DEPTH_H3, _lazy(u'H3 and higher')),
    (TOC_DEPTH_H4, _lazy('H4 and higher')),
)

# FF versions used to filter article searches, power {for} tags, etc.:
#
# Iterables of (ID, name, abbreviation for {for} tags, max version this version
# group encompasses) grouped into optgroups. To add the ability to sniff a new
# version of an existing browser (assuming it doesn't change the user agent
# string too radically), you should need only to add a line here; no JS
# required. Just be wary of inexact floating point comparisons when setting
# max_version, which should be read as "From the next smaller max_version up to
# but not including version x.y".
VersionMetadata = namedtuple('VersionMetadata',
                             'id, name, long, slug, max_version, show_in_ui')
GROUPED_FIREFOX_VERSIONS = (
    ((_lazy(u'Desktop:'), 'desktop'), (
        # The first option is the default for {for} display. This should be the
        # newest version.
        VersionMetadata(2, _lazy(u'Firefox 3.5-3.6'),
                        _lazy(u'Firefox 3.5-3.6'), 'fx35', 3.9999, True),
        VersionMetadata(1, _lazy(u'Firefox 4'),
                        _lazy(u'Firefox 4'), 'fx4', 4.9999, True),
        VersionMetadata(3, _lazy(u'Firefox 3.0'),
                        _lazy(u'Firefox 3.0'), 'fx3', 3.4999, False))),
    ((_lazy(u'Mobile:'), 'mobile'), (
        VersionMetadata(4, _lazy(u'Firefox 4'),
                        _lazy(u'Firefox 4 for Mobile'), 'm4', 4.9999, True),)))

# Flattened:  # TODO: perhaps use optgroups everywhere instead
FIREFOX_VERSIONS = tuple(chain(*[options for label, options in
                                 GROUPED_FIREFOX_VERSIONS]))

# OSes used to filter articles and declare {for} sections:
OsMetaData = namedtuple('OsMetaData', 'id, name, slug')
GROUPED_OPERATING_SYSTEMS = (
    ((_lazy(u'Desktop OS:'), 'desktop'), (
        OsMetaData(1, _lazy(u'Windows'), 'win'),
        OsMetaData(2, _lazy(u'Mac OS X'), 'mac'),
        OsMetaData(3, _lazy(u'Linux'), 'linux'))),
    ((_lazy(u'Mobile OS:'), 'mobile'), (
        OsMetaData(5, _lazy(u'Android'), 'android'),
        OsMetaData(4, _lazy(u'Maemo'), 'maemo'))))

# Flattened
OPERATING_SYSTEMS = tuple(chain(*[options for label, options in
                                  GROUPED_OPERATING_SYSTEMS]))


# how a redirect looks as rendered HTML
REDIRECT_HTML = 'REDIRECT <a class="redirect"'
REDIRECT_CONTENT = 'REDIRECT <a class="redirect" href="%(href)s">%(title)s</a>'
REDIRECT_TITLE = _lazy(u'%(old)s Redirect %(number)i')
REDIRECT_SLUG = _lazy(u'%(old)s-redirect-%(number)i')

# TODO: Put this under the control of Constance / Waffle?
# Flags used to signify revisions in need of review
REVIEW_FLAG_TAGS = (
    ('technical', _('Technical - code samples, APIs, or technologies')),
    ('editorial', _('Editorial - prose, grammar, or content')),
    ('template',  _('Template - KumaScript code')),
)
REVIEW_FLAG_TAGS_DEFAULT = ['technical', 'editorial']

# TODO: This is info derived from urls.py, but unsure how to DRY it
RESERVED_SLUGS = (
    'ckeditor_config.js$',
    'watch-ready-for-review$',
    'unwatch-ready-for-review$',
    'watch-approved$',
    'unwatch-approved$',
    '.json$',
    'new$',
    'all$',
    'templates$',
    'preview-wiki-content$',
    'category/\d+$',
    'needs-review/?[^/]+$',
    'needs-review/?',
    'feeds/[^/]+/all/?',
    'feeds/[^/]+/needs-review/[^/]+$',
    'feeds/[^/]+/needs-review/?',
    'tag/[^/]+'
)

DOCUMENT_LAST_MODIFIED_CACHE_KEY_TMPL = u'kuma:document-last-modified:%s'

DEKI_FILE_URL = re.compile(r'@api/deki/files/(?P<file_id>\d+)/=')
KUMA_FILE_URL = re.compile(r'/files/(?P<file_id>\d+)/.+\..+')


class UniqueCollision(Exception):
    """An attempt to create two pages with the same unique metadata"""
    def __init__(self, existing):
        self.existing = existing


class SlugCollision(UniqueCollision):
    """An attempt to create two pages of the same slug in one locale"""


def _inherited(parent_attr, direct_attr):
    """Return a descriptor delegating to an attr of the original document.

    If `self` is a translation, the descriptor delegates to the attribute
    `parent_attr` from the original document. Otherwise, it delegates to the
    attribute `direct_attr` from `self`.

    Use this only on a reference to another object, like a ManyToMany or a
    ForeignKey. Using it on a normal field won't work well, as it'll preclude
    the use of that field in QuerySet field lookups. Also, ModelForms that are
    passed instance=this_obj won't see the inherited value.

    """
    getter = lambda self: (getattr(self.parent, parent_attr)
                               if self.parent and
                                  self.parent.id != self.id
                           else getattr(self, direct_attr))
    setter = lambda self, val: (setattr(self.parent, parent_attr,
                                        val) if self.parent and
                                                self.parent.id != self.id else
                                setattr(self, direct_attr, val))
    return property(getter, setter)


class DocumentManager(models.Manager):
    """Manager for Documents, assists for queries"""

    def clean_content(self, content_in, use_constance_bleach_whitelists=False):
        out = (wiki.content
               .parse(content_in)
               .filterIframeHosts(constance.config.KUMA_WIKI_IFRAME_ALLOWED_HOSTS)
               .serialize())

        if use_constance_bleach_whitelists:
            tags = constance.config.BLEACH_ALLOWED_TAGS
            attributes = constance.config.BLEACH_ALLOWED_ATTRIBUTES
            styles = constance.config.BLEACH_ALLOWED_STYLES
        else:
            tags = ALLOWED_TAGS
            attributes = ALLOWED_ATTRIBUTES
            styles = ALLOWED_STYLES

        out = bleach.clean(out, attributes=attributes, tags=tags,
                           styles=styles, skip_gauntlet=True)
        return out

    def get_by_natural_key(self, locale, slug):
        return self.get(locale=locale, slug=slug)

    def allows_add_by(self, user, slug):
        """Determine whether the user can create a document with the given
        slug. Mainly for enforcing Template: editing permissions"""
        if (slug.startswith(TEMPLATE_TITLE_PREFIX) and
                not user.has_perm('wiki.add_template_document')):
            return False
        # NOTE: We could enforce wiki.add_document here, but it's implicitly
        # assumed everyone is allowed.
        return True

    def filter_for_list(self, locale=None, category=None, tag=None,
                        tag_name=None):
        docs = (self.filter(is_template=False, is_redirect=False).
                    exclude(slug__startswith='User:').
                    exclude(slug__startswith='Talk:').order_by('title'))
        if locale:
            docs = docs.filter(locale=locale)
        if category:
            try:
                docs = docs.filter(category=int(category))
            except ValueError:
                pass
        if tag:
            docs = docs.filter(tags__in=[tag])
        if tag_name:
            docs = docs.filter(tags__name=tag_name)
        # Leave out the html, since that leads to huge cache objects and we
        # never use the content in lists.
        docs = docs.defer('html')
        return docs

    def filter_for_review(self, locale=None, tag=None, tag_name=None):
        """Filter for documents with current revision flagged for review"""
        bq = 'current_revision__review_tags__%s'
        if tag_name:
            q = {bq % 'name': tag_name}
        elif tag:
            q = {bq % 'in': [tag]}
        else:
            q = {bq % 'name__isnull': False}
        if locale:
            q['locale'] = locale
        return self.filter(**q).distinct()

    def dump_json(self, queryset, stream):
        """Export a stream of JSON-serialized Documents and Revisions

        This is inspired by smuggler.views.dump_data with customizations for
        Document specifics, per bug 747137
        """
        objects = []
        for doc in queryset.all():
            rev = get_current_or_latest_revision(doc)
            if not rev:
                # Skip this doc if, for some reason, there's no revision.
                continue

            # Drop the pk and circular reference to rev.
            doc.pk = None
            doc.current_revision = None
            objects.append(doc)

            # Drop the rev pk
            rev.pk = None
            objects.append(rev)

        # HACK: This is kind of awkward, but the serializer only accepts a flat
        # list of field names across all model classes that get handled. So,
        # this is a mashup whitelist of Document and Revision fields.
        fields = (
            # TODO: Maybe make this an *exclusion* list by getting the list of
            # fields from Document and Revision models and knocking out what we
            # don't want? Serializer doesn't support exclusion list directly.
            'title', 'locale', 'slug', 'tags', 'is_template', 'is_localizable',
            'parent', 'parent_topic', 'category', 'document', 'is_redirect',
            'summary', 'content', 'comment',
            'keywords', 'tags', 'toc_depth', 'significance', 'is_approved',
            'creator',  # HACK: Replaced on import, but deserialize needs it
            'mindtouch_page_id', 'mindtouch_old_id', 'is_mindtouch_migration',
        )
        serializers.serialize('json', objects, indent=2, stream=stream,
                              fields=fields, use_natural_keys=True)

    def load_json(self, creator, stream):
        """Import a stream of JSON-serialized Documents and Revisions

        This is inspired by smuggler.views.load_data with customizations for
        Document specifics, per bug 747137
        """
        counter = 0
        objects = serializers.deserialize('json', stream)
        for obj in objects:

            # HACK: Dig up the deserializer wrapped model object & manager,
            # because the deserializer wrapper bypasses some things we need to
            # un-bypass here
            actual = obj.object
            mgr = actual._default_manager

            actual.pk = None
            if hasattr(mgr, 'get_by_natural_key'):
                # If the model uses natural keys, attempt to find the pk of an
                # existing record to overwrite.
                try:
                    nk = actual.natural_key()
                    existing = mgr.get_by_natural_key(*nk)
                    actual.pk = existing.pk
                except actual.DoesNotExist:
                    pass

            # Tweak a few fields on the way through for Revisions.
            if type(actual) is Revision:
                actual.creator = creator
                actual.created = datetime.now()

            actual.save()
            counter += 1

        return counter


class DocumentTag(TagBase):
    """A tag indexing a document"""
    class Meta:
        verbose_name = _("Document Tag")
        verbose_name_plural = _("Document Tags")


class TaggedDocument(ItemBase):
    """Through model, for tags on Documents"""
    content_object = models.ForeignKey('Document')
    tag = models.ForeignKey(DocumentTag)

    # FIXME: This is copypasta from taggit/models.py#TaggedItemBase, which I
    # don't like. But, it seems to be the only way to get *both* a custom tag
    # *and* a custom through model.
    # See: https://github.com/boar/boar/blob/master/boar/articles/models.py#L63
    @classmethod
    def tags_for(cls, model, instance=None):
        if instance is not None:
            return DocumentTag.objects.filter(
                taggeddocument__content_object=instance)
        return DocumentTag.objects.filter(
            taggeddocument__content_object__isnull=False).distinct()


class DocumentRenderingInProgress(Exception):
    """An attempt to render a page while a rendering is already in progress is
    disallowed."""
    pass


class DocumentRenderedContentNotAvailable(Exception):
    """No rendered content available, and an attempt to render on the spot was
    denied. So, the view should fall back to presenting raw content for now."""
    pass


@register_live_index
class Document(NotificationsMixin, models.Model):
    """A localized knowledgebase document, not revision-specific."""

    class Meta(object):
        unique_together = (('parent', 'locale'), ('slug', 'locale'))
        permissions = (
            ("view_document", "Can view document"),
            ("add_template_document", "Can add Template:* document"),
            ("change_template_document", "Can change Template:* document"),
            ("move_tree", "Can move a tree of documents"),
        )

    objects = DocumentManager()

    title = models.CharField(max_length=255, db_index=True)
    slug = models.CharField(max_length=255, db_index=True)

    # NOTE: Documents are indexed by tags, but tags are edited in Revisions.
    # Also, using a custom through table to isolate Document tags from those
    # used in other models and apps. (Works better than namespaces, for
    # completion and such.)
    tags = TaggableManager(through=TaggedDocument)

    # Is this document a template or not?
    is_template = models.BooleanField(default=False, editable=False,
                                      db_index=True)

    # Is this a redirect or not?
    is_redirect = models.BooleanField(default=False, editable=False,
                                      db_index=True)

    # Is this document localizable or not?
    is_localizable = models.BooleanField(default=True, db_index=True)

    # TODO: validate (against settings.SUMO_LANGUAGES?)
    locale = LocaleField(default=settings.WIKI_DEFAULT_LANGUAGE, db_index=True)

    # Latest approved revision. L10n dashboard depends on this being so (rather
    # than being able to set it to earlier approved revisions). (Remove "+" to
    # enable reverse link.)
    current_revision = models.ForeignKey('Revision', null=True,
                                         related_name='current_for+')

    # The Document I was translated from. NULL iff this doc is in the default
    # locale or it is nonlocalizable. TODO: validate against
    # settings.WIKI_DEFAULT_LANGUAGE.
    parent = models.ForeignKey('self', related_name='translations',
                               null=True, blank=True)

    parent_topic = models.ForeignKey('self', related_name='children',
                                     null=True, blank=True)

    # Related documents, based on tags in common.
    # The RelatedDocument table is populated by
    # wiki.cron.calculate_related_documents.
    related_documents = models.ManyToManyField('self',
                                               through='RelatedDocument',
                                               symmetrical=False)

    files = models.ManyToManyField('Attachment',
                                   through='DocumentAttachment')

    # JSON representation of Document for API results, built on save
    json = models.TextField(editable=False, blank=True, null=True)

    # Raw HTML of approved revision's wiki markup
    html = models.TextField(editable=False)

    # Cached result of kumascript and other offline processors (if any)
    rendered_html = models.TextField(editable=False, blank=True, null=True)

    # Errors (if any) from the last rendering run
    rendered_errors = models.TextField(editable=False, blank=True, null=True)

    # Whether or not to automatically defer rendering of this page to a queued
    # offline task. Generally used for complex pages that need time
    defer_rendering = models.BooleanField(default=False, db_index=True)

    # Timestamp when this document was last scheduled for a render
    render_scheduled_at = models.DateTimeField(null=True, db_index=True)

    # Timestamp when a render for this document was last started
    render_started_at = models.DateTimeField(null=True, db_index=True)

    # Timestamp when this document was last rendered
    last_rendered_at = models.DateTimeField(null=True, db_index=True)

    # A document's category much always be that of its parent. If it has no
    # parent, it can do what it wants. This invariant is enforced in save().
    category = models.IntegerField(choices=CATEGORIES, db_index=True)

    # Team to which this document belongs, if any
    team = models.ForeignKey(Team, blank=True, null=True)

    # HACK: Migration bookkeeping - index by the old_id of MindTouch revisions
    # so that migrations can be idempotent.
    mindtouch_page_id = models.IntegerField(
            help_text="ID for migrated MindTouch page",
            null=True, db_index=True)

    # Last modified time for the document. Should be equal-to or greater than
    # the current revision's created field
    modified = models.DateTimeField(auto_now=True, null=True, db_index=True)

    def calculate_etag(self, section_id=None):
        """Calculate an etag-suitable hash for document content or a section"""
        if not section_id:
            content = self.html
        else:
            content = (wiki.content
                       .parse(self.html)
                       .extractSection(section_id)
                       .serialize())
        return '"%s"' % hashlib.sha1(content.encode('utf8')).hexdigest()

    @property
    def is_rendering_scheduled(self):
        """Does this have a rendering scheduled?"""
        if not self.render_scheduled_at:
            return False

        # Check whether a scheduled rendering has waited for too long.  Assume
        # failure, in this case, and allow another scheduling attempt.
        timeout = constance.config.KUMA_DOCUMENT_RENDER_TIMEOUT
        max_duration = timedelta(seconds=timeout)
        duration = datetime.now() - self.render_scheduled_at
        if (duration > max_duration):
            return False

        if not self.last_rendered_at:
            return True
        return self.render_scheduled_at > self.last_rendered_at

    @property
    def is_rendering_in_progress(self):
        """Does this have a rendering in progress?"""
        if not self.render_started_at:
            # No start time, so False.
            return False

        # Check whether an in-progress rendering has gone on for too long.
        # Assume failure, in this case, and allow another rendering attempt.
        timeout = constance.config.KUMA_DOCUMENT_RENDER_TIMEOUT
        max_duration = timedelta(seconds=timeout)
        duration = datetime.now() - self.render_started_at
        if (duration > max_duration):
            return False

        if not self.last_rendered_at:
            # No rendering ever, so in progress.
            return True

        # Finally, if the render start is more recent than last completed
        # render, then we have one in progress.
        return self.render_started_at > self.last_rendered_at

    def get_rendered(self, cache_control=None, base_url=None):
        """Attempt to get rendered content for this document"""
        # No rendered content yet, so schedule the first render.
        if not self.rendered_html:
            try:
                self.schedule_rendering(cache_control, base_url)
            except DocumentRenderingInProgress:
                # Unable to trigger a rendering right now, so we bail.
                raise DocumentRenderedContentNotAvailable()

        # If we have a cache_control directive, try scheduling a render.
        if cache_control:
            try:
                self.schedule_rendering(cache_control, base_url)
            except DocumentRenderingInProgress:
                pass

        # Parse JSON errors, if available.
        errors = None
        try:
            errors = (self.rendered_errors and
                      json.loads(self.rendered_errors) or None)
        except ValueError:
            pass

        # If the above resulted in an immediate render, we might have content.
        if not self.rendered_html:
            if errors:
                return ('', errors)
            else:
                # But, no such luck, so bail out.
                raise DocumentRenderedContentNotAvailable()

        return (self.rendered_html, errors)

    def schedule_rendering(self, cache_control=None, base_url=None):
        """Attempt to schedule rendering. Honor the deferred_rendering field to
        decide between an immediate or a queued render."""
        # Avoid scheduling a rendering if already scheduled or in progress.
        if self.is_rendering_scheduled or self.is_rendering_in_progress:
            return False

        # Note when the rendering was scheduled. Kind of a hack, doing a quick
        # update and setting the local property rather than doing a save()
        now = datetime.now()
        Document.objects.filter(pk=self.pk).update(render_scheduled_at=now)
        self.render_scheduled_at = now

        if (waffle.switch_is_active('wiki_force_immediate_rendering') or
                not self.defer_rendering):
            # Attempt an immediate rendering.
            self.render(cache_control, base_url)
        else:
            # Attempt to queue a rendering. If celery.conf.ALWAYS_EAGER is
            # True, this is also an immediate rendering.
            from . import tasks
            tasks.render_document.delay(self, cache_control, base_url)

    def render(self, cache_control=None, base_url=None, timeout=None):
        """Render content using kumascript and any other services necessary."""
        # Disallow rendering while another is in progress.
        if self.is_rendering_in_progress:
            raise DocumentRenderingInProgress()

        # Note when the rendering was started. Kind of a hack, doing a quick
        # update and setting the local property rather than doing a save()
        now = datetime.now()
        Document.objects.filter(pk=self.pk).update(render_started_at=now)
        self.render_started_at = now

        # Perform rendering and update document
        if not constance.config.KUMASCRIPT_TIMEOUT:
            # A timeout of 0 should shortcircuit kumascript usage.
            self.rendered_html, self.rendered_errors = self.html, []
        else:
            self.rendered_html, errors = kumascript.get(self, cache_control,
                                                        base_url,
                                                        timeout=timeout)
            self.rendered_errors = errors and json.dumps(errors) or None

        # Finally, note the end time of rendering and update the document.
        self.last_rendered_at = datetime.now()

        # If this rendering took longer than we'd like, mark it for deferred
        # rendering in the future.
        timeout = constance.config.KUMA_DOCUMENT_FORCE_DEFERRED_TIMEOUT
        max_duration = timedelta(seconds=timeout)
        duration = self.last_rendered_at - self.render_started_at
        if (duration >= max_duration):
            self.defer_rendering = True

        # TODO: Automatically clear the defer_rendering flag if the rendering
        # time falls under the limit? Probably safer to require manual
        # intervention to free docs from deferred jail.

        self.save()
        render_done.send(sender=self.__class__, instance=self)

    def get_summary(self, strip_markup=True, use_rendered=True):
        """Attempt to get the document summary from rendered content, with
        fallback to raw HTML"""
        if use_rendered and self.rendered_html:
            src = self.rendered_html
        else:
            src = self.html
        summary = wiki.content.get_seo_description(src, self.locale,
                                                   strip_markup)
        return summary

    def build_json_data(self):
        content = (wiki.content.parse(self.html)
                               .injectSectionIDs()
                               .serialize())
        sections = wiki.content.get_content_sections(content)

        summary = ''
        if self.current_revision:
            if self.current_revision.summary:
                summary = self.current_revision.summary
            else:
                summary = self.get_summary(strip_markup=False)

        translations = []
        if self.pk:
            for translation in self.other_translations:
                translations.append({
                    'locale': translation.locale,
                    'title': translation.title,
                    'url': reverse('wiki.document', args=[translation.full_path],
                                   locale=translation.locale)
                })

        if not self.current_revision:
            review_tags = []
        else:
            review_tags = [x.name for x in
                           self.current_revision.review_tags.all()]
        if not self.pk:
            tags = []
        else:
            tags = [x.name for x in self.tags.all()]

        if self.modified:
            modified = self.modified.isoformat()
        else:
            modified = datetime.now().isoformat()

        return {
            'title': self.title,
            'label': self.title,
            'url': self.get_absolute_url(),
            'id': self.id,
            'slug': self.slug,
            'tags': tags,
            'review_tags': review_tags,
            'sections': sections,
            'locale': self.locale,
            'summary': summary,
            'translations': translations,
            'modified': modified,
            'json_modified': datetime.now().isoformat()
        }

    def get_json_data(self, stale=True):
        """Returns a document in object format for output as JSON.

        The stale parameter, when True, accepts stale cached data even after
        the document has been modified."""

        # Have parsed data & don't care about freshness? Here's a quick out..
        curr_json_data = getattr(self, '_json_data', None)
        if curr_json_data and stale:
            return curr_json_data

        # Attempt to parse the current contents of self.json, taking care in
        # case it's empty or broken JSON.
        self._json_data = {}
        if self.json:
            try:
                self._json_data = json.loads(self.json)
            except (TypeError, ValueError):
                pass

        # Try to get ISO 8601 datestamps for the doc and the json
        json_lmod = self._json_data.get('json_modified', '')
        doc_lmod = self.modified.isoformat()

        # If there's no parsed data or the data is stale & we care, it's time
        # to rebuild the cached JSON data.
        if (not self._json_data) or (not stale and doc_lmod > json_lmod):
            old_json = self.json
            self._json_data = self.build_json_data()
            self.json = json.dumps(self._json_data)
            # HACK: Update just the json field for the document.
            Document.objects.filter(pk=self.pk).update(json=self.json)

        return self._json_data

    def extract_code_sample(self, id):
        """Given the id of a code sample, attempt to extract it from rendered
        HTML with a fallback to non-rendered in case of errors."""
        try:
            src, errors = self.get_rendered()
            if errors:
                src = self.html
        except:
            src = self.html
        return wiki.content.extract_code_sample(id, src)

    def natural_key(self):
        return (self.locale, self.slug,)

    @property
    def natural_cache_key(self):
        nk = u'/'.join(self.natural_key())
        return hashlib.md5(nk.encode('utf8')).hexdigest()

    def _existing(self, attr, value):
        """Return an existing doc (if any) in this locale whose `attr` attr is
        equal to mine."""
        return Document.objects.filter(locale=self.locale,
                                        **{attr: value})

    def _raise_if_collides(self, attr, exception):
        """Raise an exception if a page of this title/slug already exists."""
        if self.id is None or hasattr(self, 'old_' + attr):
            # If I am new or my title/slug changed...
            existing = self._existing(attr, getattr(self, attr))
            if existing.exists():
                raise exception(existing[0])

    def clean(self):
        """Translations can't be localizable."""
        self._clean_is_localizable()
        self._clean_category()

    def _clean_is_localizable(self):
        """is_localizable == allowed to have translations. Make sure that isn't
        violated.

        For default language (en-US), is_localizable means it can have
        translations. Enforce:
            * is_localizable=True if it has translations
            * if has translations, unable to make is_localizable=False

        For non-default langauges, is_localizable must be False.

        """
        if self.locale != settings.WIKI_DEFAULT_LANGUAGE:
            self.is_localizable = False

        # Can't save this translation if parent not localizable
        if (self.parent and self.parent.id != self.id and
                not self.parent.is_localizable):
            raise ValidationError('"%s": parent "%s" is not localizable.' % (
                                  unicode(self), unicode(self.parent)))

        # Can't make not localizable if it has translations
        # This only applies to documents that already exist, hence self.pk
        if self.pk and not self.is_localizable and self.translations.exists():
            raise ValidationError('"%s": document has %s translations but is '
                                  'not localizable.' % (
                                  unicode(self), self.translations.count()))

    def _clean_category(self):
        """Make sure a doc's category is the same as its parent's."""
        parent = self.parent
        if parent:
            self.category = parent.category
        elif self.category not in (id for id, name in CATEGORIES):
            # All we really need to do here is make sure category != '' (which
            # is what it is when it's missing from the DocumentForm). The extra
            # validation is just a nicety.
            raise ValidationError(_('Please choose a category.'))
        else:  # An article cannot have both a parent and children.
            # Make my children the same as me:
            if self.id:
                self.translations.all().update(category=self.category)

    def _attr_for_redirect(self, attr, template):
        """Return the slug or title for a new redirect.

        `template` is a Python string template with "old" and "number" tokens
        used to create the variant.

        """
        def unique_attr():
            """Return a variant of getattr(self, attr) such that there is no
            Document of my locale with string attribute `attr` equal to it.

            Never returns the original attr value.

            """
            # "My God, it's full of race conditions!"
            i = 1
            while True:
                new_value = template % dict(old=getattr(self, attr), number=i)
                if not self._existing(attr, new_value).exists():
                    return new_value
                i += 1

        old_attr = 'old_' + attr
        if hasattr(self, old_attr):
            # My slug (or title) is changing; we can reuse it for the redirect.
            return getattr(self, old_attr)
        else:
            # Come up with a unique slug (or title):
            return unique_attr()

    def revert(self, revision, user, comment=None):
        old_review_tags = [t.name for t in revision.review_tags.all()]
        if revision.document.original == self:
            revision.based_on = revision
        revision.id = None
        revision.comment = "Revert to revision of %s by %s" % (
                revision.created, revision.creator)
        if comment:
            revision.comment += ': "%s"' % comment
        revision.created = datetime.now()
        revision.creator = user
        revision.save()
        if old_review_tags:
            revision.review_tags.set(*old_review_tags)
        revision.make_current()
        return revision

    def revise(self, user, data, section_id=None):
        """Given a dict of changes to make, build and save a new Revision to
        revise this document"""
        curr_rev = self.current_revision
        new_rev = Revision(creator=user, document=self, content=self.html)
        for n in ('title', 'slug', 'category'):
            setattr(new_rev, n, getattr(self, n))
        if curr_rev:
            new_rev.toc_depth = curr_rev.toc_depth
            original_doc = curr_rev.document.original
            if original_doc == self:
                new_rev.based_on = curr_rev
            else:
                new_rev.based_on = original_doc.current_revision

        # Accept optional field edits...

        new_title = data.get('title', False)
        new_rev.title = (new_title and new_title or self.title)

        new_tags = data.get('tags', False)
        new_rev.tags = (new_tags and new_tags or
                        edit_string_for_tags(self.tags.all()))

        new_review_tags = data.get('review_tags', False)
        if new_review_tags:
            review_tags = new_review_tags
        elif curr_rev:
            review_tags = edit_string_for_tags(curr_rev.review_tags.all())
        else:
            review_tags = ''

        new_rev.summary = data.get('summary', '')

        # Accept HTML edits, optionally by section
        new_html = data.get('content', data.get('html', False))
        if new_html:
            if not section_id:
                new_rev.content = new_html
            else:
                new_rev.content = (wiki.content.parse(self.html)
                                   .replaceSection(section_id, new_html)
                                   .serialize())

        # Finally, commit the revision changes and return the new rev.
        new_rev.save()
        new_rev.review_tags.set(*parse_tags(review_tags))
        return new_rev

    def save(self, *args, **kwargs):
        self.is_template = self.slug.startswith(TEMPLATE_TITLE_PREFIX)
        self.is_redirect = 1 if self.redirect_url() else 0

        try:
            # Check if the slug would collide with an existing doc
            self._raise_if_collides('slug', SlugCollision)
        except UniqueCollision, e:
            if e.existing.redirect_url() is not None:
                # If the existing doc is a redirect, delete it and clobber it.
                e.existing.delete()
            else:
                raise e

        # These are too important to leave to a (possibly omitted) is_valid
        # call:
        self._clean_is_localizable()
        # Everything is validated before save() is called, so the only thing
        # that could cause save() to exit prematurely would be an exception,
        # which would cause a rollback, which would negate any category changes
        # we make here, so don't worry:
        self._clean_category()

        if not self.parent_topic and self.parent:
            # If this is a translation without a topic parent, try to get one.
            self.acquire_translated_topic_parent()

        super(Document, self).save(*args, **kwargs)

        # Delete any cached last-modified timestamp.
        cache_key = (DOCUMENT_LAST_MODIFIED_CACHE_KEY_TMPL %
                     self.natural_cache_key)
        cache.delete(cache_key)

        # Make redirects if there's an approved revision and title or slug
        # changed. Allowing redirects for unapproved docs would (1) be of
        # limited use and (2) require making Revision.creator nullable.
        slug_changed = hasattr(self, 'old_slug')
        title_changed = hasattr(self, 'old_title')
        if self.current_revision and slug_changed:
            self.move()
            if slug_changed:
                del self.old_slug
        if title_changed:
            del self.old_title

    def delete(self, *args, **kwargs):
        if waffle.switch_is_active('wiki_error_on_delete'):
            # bug 863692: Temporary while we investigate disappearing pages.
            raise Exception("Attempt to delete document %s: %s" % (self.id, self.title))
        else:
            super(Document, self).delete(*args, **kwargs)

    def move(self, new_slug=None, user=None):
        """
        Complete the process of moving a page by leaving a redirect
        behind.

        """
        if new_slug is None:
            new_slug = self.slug
        if user is None:
            user = self.current_revision.creator
        self.slug = new_slug
        doc = Document.objects.create(locale=self.locale,
                                      title=self._attr_for_redirect(
                                          'title', REDIRECT_TITLE),
                                      slug=self._attr_for_redirect(
                                          'slug', REDIRECT_SLUG),
                                      category=self.category,
                                      is_localizable=False)
        Revision.objects.create(document=doc,
                                content=REDIRECT_CONTENT % dict(
                                    href=self.get_absolute_url(),
                                    title=self.title),
                                is_approved=True,
                                toc_depth=self.current_revision.toc_depth,
                                reviewer=self.current_revision.creator,
                                creator=user)

    def _tree_conflicts(self, new_slug):
        """
        Given a new slug to be assigned to this document, return a
        list of documents (if any) which would be overwritten by
        moving this document or any of its children in that fashion.

        """
        conflicts = []
        try:
            existing = Document.objects.get(locale=self.locale, slug=new_slug)
            if not existing.redirect_url():
                conflicts.append(existing)
        except Document.DoesNotExist:
            pass
        for child in self.get_descendants():
            child_title = child.slug.split('/')[-1]
            try:
                existing = Document.objects.get(locale=self.locale,
                                        slug='/'.join([new_slug, child_title]))
                if not existing.redirect_url():
                    conflicts.append(existing)
            except Document.DoesNotExist:
                pass
        return conflicts

    def _move_tree(self, new_slug, user=None, title=None):
        """
        Move this page and all its children.

        """
        old_slug = self.slug

        if user is None:
            user = self.current_revision.creator

        rev = self.current_revision
        review_tags = [str(tag) for tag in rev.review_tags.all()]

        # Shortcut trick for getting an object with all the same
        # values, but making Django think it's new.
        rev.id = None

        rev.creator = user
        rev.created = datetime.now()
        rev.slug = new_slug
        if title:
            rev.title = title

        rev.save(force_insert=True)

        rev.review_tags.set(*review_tags)

        for child in self.children.all():
            child_title = child.slug.split('/')[-1]
            child._move_tree('/'.join([new_slug, child_title]), user)

    def acquire_translated_topic_parent(self):
        """This normalizes topic breadcrumb paths between locales.

        Attempt to acquire a topic parent from a translation of our translation
        parent's topic parent, auto-creating a stub document if necessary."""
        if not self.parent:
            # Bail, if this is not in fact a translation.
            return
        ppt = self.parent.parent_topic
        if not ppt:
            # Bail, if the translation parent has no topic parent
            return
        try:
            # Look for an existing translation of the topic parent
            new_pt = ppt.translations.get(locale=self.locale)
        except Document.DoesNotExist:
            try:
                # No luck. As a longshot, let's try looking for the same slug.
                new_pt = (Document.objects.get(locale=self.locale,
                                               slug=ppt.slug))
                if not new_pt.parent:
                    # HACK: This same-slug/different-locale doc should probably
                    # be considered a translation. Let's correct that on the
                    # spot.
                    new_pt.parent = ppt
                    new_pt.save()
            except Document.DoesNotExist:
                # Finally, let's create a translated stub for a topic parent
                new_pt = (Document.objects
                          .get(pk=ppt.pk))
                new_pt.pk = None
                new_pt.current_revision = None
                new_pt.parent_topic = None
                new_pt.parent = ppt
                new_pt.locale = self.locale
                new_pt.save()

                if ppt.current_revision:
                    # Don't forget to clone a current revision
                    new_rev = (Revision.objects
                               .get(pk=ppt.current_revision.pk))
                    new_rev.pk = None
                    new_rev.document = new_pt
                    # HACK: Let's auto-add tags that flag this as a topic stub
                    addl_tags = '"TopicStub","NeedsTranslation"'
                    if new_rev.tags:
                        new_rev.tags = '%s,%s' % (new_rev.tags, addl_tags)
                    else:
                        new_rev.tags = addl_tags
                    new_rev.save()

        # Finally, assign the new default parent topic
        self.parent_topic = new_pt

    def __setattr__(self, name, value):
        """Trap setting slug and title, recording initial value."""
        # Public API: delete the old_title or old_slug attrs after changing
        # title or slug (respectively) to suppress redirect generation.
        if getattr(self, 'id', None):
            # I have been saved and so am worthy of a redirect.
            if name in ('slug', 'title') and hasattr(self, name):
                old_name = 'old_' + name
                if not hasattr(self, old_name):
                    # Case insensitive comparison:
                    if getattr(self, name).lower() != value.lower():
                        # Save original value:
                        setattr(self, old_name, getattr(self, name))
                elif value == getattr(self, old_name):
                    # They changed the attr back to its original value.
                    delattr(self, old_name)
        super(Document, self).__setattr__(name, value)

    @property
    def content_parsed(self):
        if not self.current_revision:
            return None

        return self.current_revision.content_parsed

    def files_dict(self):
        intermediates = DocumentAttachment.objects.filter(document__pk=self.id)
        files = {}
        for f in intermediates:
            attachment = f.file
            rev = attachment.current_revision
            files[f.name] = {'attached_by': f.attached_by.username,
                             'creator': rev.creator.username,
                             'description': rev.description,
                             'mime_type': rev.mime_type,
                             'html': attachment.get_embed_html(),
                             'url': attachment.get_file_url()}
        return files

    @property
    def attachments(self):
        # Is there a more elegant way to do this?
        #
        # File attachments aren't really stored at the DB level;
        # instead, the page just gets appropriate HTML to embed
        # whatever type of file it is. So we find them by
        # regex-searching over the HTML for URLs that match the
        # file URL patterns.
        mt_files = DEKI_FILE_URL.findall(self.html)
        kuma_files = KUMA_FILE_URL.findall(self.html)
        mt_q = kuma_q = params = None

        if mt_files:
            # We have at least some MindTouch files.
            params = models.Q(mindtouch_attachment_id__in=mt_files)
            if kuma_files:
                # We also have some kuma files. Use an OR query.
                params = params | models.Q(id__in=kuma_files)
        if kuma_files and not params:
            # We have only kuma files.
            params = models.Q(id__in=kuma_files)
        if params:
            return Attachment.objects.filter(params)
        # If no files found, return an empty Attachment queryset.
        return Attachment.objects.none()

    @property
    def show_toc(self):
        return self.current_revision and self.current_revision.toc_depth

    @property
    def language(self):
        return settings.LANGUAGES[self.locale.lower()]

    # FF version and OS are hung off the original, untranslated document and
    # dynamically inherited by translations:
    firefox_versions = _inherited('firefox_versions', 'firefox_version_set')
    operating_systems = _inherited('operating_systems', 'operating_system_set')

    @property
    def full_path(self):
        """The full path of a document consists of {slug}"""
        # TODO: See about removing this and all references to full_path? Once
        # upon a time, this was composed of {locale}/{slug}, but bug 754534
        # reverted that.
        return self.slug

    def get_absolute_url(self, ui_locale=None):
        """Build the absolute URL to this document from its full path"""
        if not ui_locale:
            ui_locale = self.locale
        return reverse('wiki.document', locale=ui_locale,
                       args=[self.full_path])

    @staticmethod
    def locale_and_slug_from_path(path, request=None, path_locale=None):
        """Given a proposed doc path, try to see if there's a legacy MindTouch
        locale or even a modern Kuma domain in the path. If so, signal for a
        redirect to a more canonical path. In any case, produce a locale and
        slug derived from the given path."""
        locale, slug, needs_redirect = '', path, False
        mdn_languages_lower = dict((x.lower(), x)
                                   for x in settings.MDN_LANGUAGES)

        # If there's a slash in the path, then the first segment could be a
        # locale. And, that locale could even be a legacy MindTouch locale.
        if '/' in path:
            maybe_locale, maybe_slug = path.split('/', 1)
            l_locale = maybe_locale.lower()

            if l_locale in settings.MT_TO_KUMA_LOCALE_MAP:
                # The first segment looks like a MindTouch locale, remap it.
                needs_redirect = True
                locale = settings.MT_TO_KUMA_LOCALE_MAP[l_locale]
                slug = maybe_slug

            elif l_locale in mdn_languages_lower:
                # The first segment looks like an MDN locale, redirect.
                needs_redirect = True
                locale = mdn_languages_lower[l_locale]
                slug = maybe_slug

        # No locale yet? Try the locale detected by the request or in path
        if locale == '':
            if request:
                locale = request.locale
            elif path_locale:
                locale = path_locale

        # Still no locale? Probably no request. Go with the site default.
        if locale == '':
            locale = getattr(settings, 'WIKI_DEFAULT_LANGUAGE', 'en-US')

        return (locale, slug, needs_redirect)

    @staticmethod
    def from_url(url, required_locale=None, id_only=False):
        """Return the approved Document the URL represents, None if there isn't
        one.

        Return None if the URL is a 404, the URL doesn't point to the right
        view, or the indicated document doesn't exist.

        To limit the universe of discourse to a certain locale, pass in a
        `required_locale`. To fetch only the ID of the returned Document, set
        `id_only` to True.

        """
        # Extract locale and path from URL:
        path = urlparse(url)[2]  # never has errors AFAICT
        locale, path = split_path(path)
        if required_locale and locale != required_locale:
            return None
        path = '/' + path

        try:
            view, view_args, view_kwargs = resolve(path)
        except Http404:
            return None

        import wiki.views  # Views import models; models import views.
        if view != wiki.views.document:
            return None

        # Map locale-slug pair to Document ID:
        doc_query = Document.objects.exclude(current_revision__isnull=True)
        if id_only:
            doc_query = doc_query.only('id')
        try:
            return doc_query.get(
                locale=locale,
                slug=view_kwargs['document_slug'])
        except Document.DoesNotExist:
            return None

    def redirect_url(self):
        """If I am a redirect, return the absolute URL to which I redirect.

        Otherwise, return None.

        """
        # If a document starts with REDIRECT_HTML and contains any <a> tags
        # with hrefs, return the href of the first one. This trick saves us
        # from having to parse the HTML every time.
        if REDIRECT_HTML in self.html:
            anchors = PyQuery(self.html)('a[href].redirect')
            if anchors:
                return anchors[0].get('href')

    def redirect_document(self):
        """If I am a redirect to a Document, return that Document.

        Otherwise, return None.

        """
        url = self.redirect_url()
        if url:
            return self.from_url(url)

    def __unicode__(self):
        return u'%s (%s)' % (self.get_absolute_url(), self.title)

    def filter_permissions(self, user, permissions):
        """Filter permissions with custom logic"""
        # No-op, for now.
        return permissions

    def get_topic_parents(self):
        """Build a list of parent topics from self to root"""
        curr, parents = self, []
        while curr.parent_topic:
            curr = curr.parent_topic
            parents.append(curr)
        return parents

    def get_permission_parents(self):
        return self.get_topic_parents()

    def find_zone_stack(self):
        """Assemble the stack of DocumentZones available from this document,
        moving up the stack of topic parents"""
        stack = []
        try:
            stack.append(DocumentZone.objects.get(document=self))
        except DocumentZone.DoesNotExist:
            pass
        for p in self.get_topic_parents():
            try:
                stack.append(DocumentZone.objects.get(document=p))
            except DocumentZone.DoesNotExist:
                pass
        return stack

    def allows_revision_by(self, user):
        """Return whether `user` is allowed to create new revisions of me.

        The motivation behind this method is that templates and other types of
        docs may have different permissions.

        """
        if (self.slug.startswith(TEMPLATE_TITLE_PREFIX) and
                not user.has_perm('wiki.change_template_document')):
            return False
        return True

    def allows_editing_by(self, user):
        """Return whether `user` is allowed to edit document-level metadata.

        If the Document doesn't have a current_revision (nothing approved) then
        all the Document fields are still editable. Once there is an approved
        Revision, the Document fields can only be edited by privileged users.

        """
        if (self.slug.startswith(TEMPLATE_TITLE_PREFIX) and
                not user.has_perm('wiki.change_template_document')):
            return False
        return (not self.current_revision or
                user.has_perm('wiki.change_document'))

    def translated_to(self, locale):
        """Return the translation of me to the given locale.

        If there is no such Document, return None.

        """
        if self.locale != settings.WIKI_DEFAULT_LANGUAGE:
            raise NotImplementedError('translated_to() is implemented only on'
                                      'Documents in the default language so'
                                      'far.')
        try:
            return Document.objects.get(locale=locale, parent=self)
        except Document.DoesNotExist:
            return None

    @property
    def original(self):
        """Return the document I was translated from or, if none, myself."""
        return self.parent or self

    @property
    def other_translations(self):
        """Return a list of Documents - other translations of this Document"""
        translations = []
        if self.parent == None:
            translations = list(self.translations.all().order_by('locale'))
        else:
            translations = list(self.parent.translations.all().
                                exclude(id=self.id).order_by('locale'))
            translations.insert(0, self.parent)
        return translations

    @property
    def parents(self):
        """Return the list of topical parent documents above this one,
        or an empty list if none exist."""
        if self.parent_topic is None:
            return []
        current_parent = self.parent_topic
        parents = [current_parent]
        while current_parent.parent_topic is not None:
            parents.insert(0, current_parent.parent_topic)
            current_parent = current_parent.parent_topic
        return parents

    def has_children(self):
        """Does this document have at least one child?"""
        return self.children.count()

    def is_child_of(self, other):
        """Circular dependency detection -- if someone tries to set
        this as a parent of a document it's a child of, they're gonna
        have a bad time."""
        return other.id in (d.id for d in self.parents)

    # This is a method, not a property, because it can do a lot of DB
    # queries and so should look scarier. It's not just named
    # 'children' because that's taken already by the reverse relation
    # on parent_topic.
    def get_descendants(self, limit=None, levels=0):
        """Return a list of all documents which are children
        (grandchildren, great-grandchildren, etc.) of this one."""
        results = []

        if (limit is None or levels < limit) and self.has_children():
            for child in self.children.all():
                results.append(child)
                [results.append(grandchild) for \
                 grandchild in child.get_descendants(limit, levels + 1)]
        return results

    def has_voted(self, request):
        """Did the user already vote for this document?"""
        if request.user.is_authenticated():
            qs = HelpfulVote.objects.filter(document=self,
                                            creator=request.user)
        elif request.anonymous.has_id:
            anon_id = request.anonymous.anonymous_id
            qs = HelpfulVote.objects.filter(document=self,
                                            anonymous_id=anon_id)
        else:
            return False

        return qs.exists()

    def is_majorly_outdated(self):
        """Return whether a MAJOR_SIGNIFICANCE-level update has occurred to the
        parent document since this translation had an approved update.

        If this is not a translation or has never been approved, return False.

        """
        if not (self.parent and self.current_revision):
            return False

        based_on_id = self.current_revision.based_on_id
        more_filters = {'id__gt': based_on_id} if based_on_id else {}
        return self.parent.revisions.filter(
            is_approved=True,
            significance__gte=MAJOR_SIGNIFICANCE, **more_filters).exists()

    def is_watched_by(self, user):
        """Return whether `user` is notified of edits to me."""
        from wiki.events import EditDocumentEvent
        return EditDocumentEvent.is_notifying(user, self)

    def get_mapping_type(self):
        return DocumentType


@register_mapping_type
class DocumentType(SearchMappingType, Indexable):

    excerpt_fields = ['summary', 'content']

    @classmethod
    def get_model(cls):
        return Document

    @classmethod
    def extract_document(cls, obj_id, obj=None):
        if obj is None:
            obj = cls.get_model().objects.get(pk=obj_id)

        return {
            'id': obj.id,
            'title': obj.title,
            'slug': obj.slug,
            'summary': obj.get_summary(strip_markup=True),
            'locale': obj.locale,
            'modified': obj.modified,
            'content': strip_tags(obj.rendered_html),
            'tags': [tag.name for tag in obj.tags.all()]
        }

    @classmethod
    def get_mapping(cls):
        return {
            'id': {'type': 'integer'},
            'title': {'type': 'string'},
            'slug': {'type': 'string'},
            'summary': {'type': 'string', 'analyzer': 'snowball'},
            'locale': {'type': 'string', 'index': 'not_analyzed'},
            'modified': {'type': 'date'},
            'content': {'type': 'string', 'analyzer': 'wikiMarkup'},
            'tags': {'type': 'string', 'analyzer': 'snowball'},
        }

    @classmethod
    def get_indexable(cls):
        model = cls.get_model()
        return (model.objects
                    .filter(is_template=0,
                            is_redirect=0)
                    .exclude(slug__icontains='Talk:')
                    .values_list('id', flat=True)
               )

    @classmethod
    def get_analysis(cls):
        return {
            'analyzer': {
                'wikiMarkup': {
                    'type': 'standard',
                    'char_filter': 'html_strip'
                }
            }
        }

    def get_excerpt(self):
        def bleach_matches(matches):
            bleached_matches = []
            for match in matches:
                bleached_matches.append(bleach.clean(match,
                                                     tags=['em',],
                                                     strip=True)
                                       )
            return bleached_matches

        stripped_matches = []
        for field in self.excerpt_fields:
            if field in self._highlight:
                stripped_matches = bleach_matches(self._highlight[field])
                return u'...'.join(stripped_matches)
        if not stripped_matches:
            return self.summary
        return u'...'.join(stripped_matches)


class DocumentZone(models.Model):
    """Model object declaring a content zone root at a given Document, provides
    attributes inherited by the topic hierarchy beneath it."""
    document = models.ForeignKey(Document, related_name='zones', unique=True)
    styles = models.TextField(null=True, blank=True)


class ReviewTag(TagBase):
    """A tag indicating review status, mainly for revisions"""
    class Meta:
        verbose_name = _("Review Tag")
        verbose_name_plural = _("Review Tags")


class ReviewTaggedRevision(ItemBase):
    """Through model, just for review tags on revisions"""
    content_object = models.ForeignKey('Revision')
    tag = models.ForeignKey(ReviewTag)

    # FIXME: This is copypasta from taggit/models.py#TaggedItemBase, which I
    # don't like. But, it seems to be the only way to get *both* a custom tag
    # *and* a custom through model.
    # See: https://github.com/boar/boar/blob/master/boar/articles/models.py#L63
    @classmethod
    def tags_for(cls, model, instance=None):
        if instance is not None:
            return ReviewTag.objects.filter(
                reviewtaggedrevision__content_object=instance)
        return ReviewTag.objects.filter(
            reviewtaggedrevision__content_object__isnull=False).distinct()


class Revision(models.Model):
    """A revision of a localized knowledgebase document"""
    document = models.ForeignKey(Document, related_name='revisions')

    # Title and slug in document are primary, but they're kept here for
    # revision history.
    title = models.CharField(max_length=255, null=True, db_index=True)
    slug = models.CharField(max_length=255, null=True, db_index=True)

    summary = models.TextField()  # wiki markup
    content = models.TextField()  # wiki markup

    # Keywords are used mostly to affect search rankings. Moderators may not
    # have the language expertise to translate keywords, so we put them in the
    # Revision so the translators can handle them:
    keywords = models.CharField(max_length=255, blank=True)

    # Tags are stored in a Revision as a plain CharField, because Revisions are
    # not indexed by tags. This data is retained for history tracking.
    tags = models.CharField(max_length=255, blank=True)

    # Tags are (ab)used as status flags and for searches, but the through model
    # should constrain things from getting expensive.
    review_tags = TaggableManager(through=ReviewTaggedRevision)

    toc_depth = models.IntegerField(choices=TOC_DEPTH_CHOICES,
                                    default=TOC_DEPTH_ALL)

    created = models.DateTimeField(default=datetime.now, db_index=True)
    reviewed = models.DateTimeField(null=True)
    significance = models.IntegerField(choices=SIGNIFICANCES, null=True)
    comment = models.CharField(max_length=255)
    reviewer = models.ForeignKey(User, related_name='reviewed_revisions',
                                 null=True)
    creator = models.ForeignKey(User, related_name='created_revisions')
    is_approved = models.BooleanField(default=True, db_index=True)

    # The default locale's rev that was current when the Edit button was hit to
    # create this revision. Used to determine whether localizations are out of
    # date.
    based_on = models.ForeignKey('self', null=True, blank=True)
    # TODO: limit_choices_to={'document__locale':
    # settings.WIKI_DEFAULT_LANGUAGE} is a start but not sufficient.

    # HACK: Migration bookkeeping - index by the old_id of MindTouch revisions
    # so that migrations can be idempotent.
    mindtouch_old_id = models.IntegerField(
            help_text="ID for migrated MindTouch revision (null for current)",
            null=True, db_index=True, unique=True)
    is_mindtouch_migration = models.BooleanField(default=False, db_index=True,
            help_text="Did this revision come from MindTouch?")

    def get_absolute_url(self):
        """Build the absolute URL to this revision"""
        return reverse('wiki.revision', locale=self.document.locale,
                       args=[self.document.full_path, self.pk])

    def _based_on_is_clean(self):
        """Return a tuple: (the correct value of based_on, whether the old
        value was correct).

        based_on must be an approved revision of the English version of the
        document if there are any such revisions, any revision if no
        approved revision exists, and None otherwise. If based_on is not
        already set when this is called, the return value defaults to the
        current_revision of the English document.

        """
        # TODO(james): This could probably be simplified down to "if
        # based_on is set, it must be a revision of the original document."
        original = self.document.original
        base = get_current_or_latest_revision(original)
        has_approved = original.revisions.filter(is_approved=True).exists()
        if (original.current_revision or not has_approved):
            if (self.based_on and self.based_on.document != original):
                # based_on is set and points to the wrong doc.
                return base, False
            # Else based_on is valid; leave it alone.
        elif self.based_on:
            return None, False
        return self.based_on, True

    def clean(self):
        """Ensure based_on is valid."""
        # All of the cleaning herein should be unnecessary unless the user
        # messes with hidden form data.
        try:
            self.document and self.document.original
        except Document.DoesNotExist:
            # For clean()ing forms that don't have a document instance behind
            # them yet
            self.based_on = None
        else:
            based_on, is_clean = self._based_on_is_clean()
            if not is_clean:
                if self.document.parent:
                    # Restoring translation source, so base on current_revision
                    self.based_on = self.document.parent.current_revision
                else:
                    old = self.based_on
                    self.based_on = based_on  # Guess a correct value.
                    locale = LOCALES[settings.WIKI_DEFAULT_LANGUAGE].native
                    # TODO(erik): This error message ignores non-translations.
                    raise ValidationError(_('A revision must be based on a '
                        'revision of the %(locale)s document. Revision ID'
                        ' %(id)s does not fit those criteria.') %
                        dict(locale=locale, id=old.id))

    def save(self, *args, **kwargs):
        _, is_clean = self._based_on_is_clean()
        if not is_clean:  # No more Mister Nice Guy
            # TODO(erik): This error message ignores non-translations.
            raise ProgrammingError('Revision.based_on must be None or refer '
                                   'to a revision of the default-'
                                   'language document. It was %s' %
                                   self.based_on)

        if not self.title:
            self.title = self.document.title
        if not self.slug:
            self.slug = self.document.slug

        if self.is_approved and not self.reviewed:
            # HACK: For Kuma, we do an end-run around the review system here by
            # auto-self-reviewing all revisions.
            # TODO: Remove the kitsune review/approval system from kuma.
            self.reviewer = self.creator
            self.reviewed = datetime.now()

        super(Revision, self).save(*args, **kwargs)

        # When a revision is approved, update document metadata and re-cache
        # the document's html content
        if self.is_approved:
            self.make_current()

    def make_current(self):
        """Make this revision the current one for the document"""
        self.document.title = self.title
        self.document.slug = self.slug
        self.document.html = self.content_cleaned
        self.document.current_revision = self

        # Since Revision stores tags as a string, we need to parse them first
        # before setting on the Document.
        self.document.tags.set(*parse_tags(self.tags))

        self.document.save()

    def __unicode__(self):
        return u'[%s] %s #%s: %s' % (self.document.locale,
                                      self.document.title,
                                      self.id, self.content[:50])

    def get_section_content(self, section_id):
        """Convenience method to extract the content for a single section"""
        return(wiki.content
            .parse(self.content)
            .extractSection(section_id)
            .serialize())

    @property
    def content_cleaned(self):
        if self.document.is_template:
            return self.content
        return Document.objects.clean_content(self.content)

    def get_previous(self):
        previous_revisions = self.document.revisions.filter(
                                is_approved=True,
                                created__lt=self.created,
                                ).order_by('-created')
        if len(previous_revisions):
            return previous_revisions[0]
        else:
            return None

    def needs_editorial_review(self):
        return 'editorial' in [t.name for t in self.review_tags.all()]

    def needs_technical_review(self):
        return 'technical' in [t.name for t in self.review_tags.all()]


# FirefoxVersion and OperatingSystem map many ints to one Document. The
# enumeration table of int-to-string is not represented in the DB because of
# difficulty working DB-dwelling gettext keys into our l10n workflow.
class FirefoxVersion(models.Model):
    """A Firefox version, version range, etc. used to categorize documents"""
    item_id = models.IntegerField(choices=[(v.id, v.name) for v in
                                           FIREFOX_VERSIONS])
    document = models.ForeignKey(Document, related_name='firefox_version_set')

    class Meta(object):
        unique_together = ('item_id', 'document')


class OperatingSystem(models.Model):
    """An operating system used to categorize documents"""
    item_id = models.IntegerField(choices=[(o.id, o.name) for o in
                                           OPERATING_SYSTEMS])
    document = models.ForeignKey(Document, related_name='operating_system_set')

    class Meta(object):
        unique_together = ('item_id', 'document')


class HelpfulVote(models.Model):
    """Helpful or Not Helpful vote on Document."""
    document = models.ForeignKey(Document, related_name='poll_votes')
    helpful = models.BooleanField(default=False)
    created = models.DateTimeField(default=datetime.now, db_index=True)
    creator = models.ForeignKey(User, related_name='poll_votes', null=True)
    anonymous_id = models.CharField(max_length=40, db_index=True)
    user_agent = models.CharField(max_length=1000)


class RelatedDocument(models.Model):
    document = models.ForeignKey(Document, related_name='related_from')
    related = models.ForeignKey(Document, related_name='related_to')
    in_common = models.IntegerField()

    class Meta(object):
        ordering = ['-in_common']


def toolbar_config_upload_to(instance, filename):
    """upload_to builder for toolbar config files"""
    if (instance.default and instance.default == True):
        return 'js/ckeditor_config.js'
    else:
        return 'js/ckeditor_config_%s.js' % instance.creator.id


class EditorToolbar(models.Model):
    creator = models.ForeignKey(User, related_name='created_toolbars')
    default = models.BooleanField(default=False)
    name = models.CharField(max_length=100)
    code = models.TextField(max_length=2000)

    def __unicode__(self):
        return self.name


def get_current_or_latest_revision(document, reviewed_only=True):
    """Returns current revision if there is one, else the last created
    revision."""
    rev = document.current_revision
    if not rev:
        if reviewed_only:
            filter = models.Q(is_approved=False, reviewed__isnull=False)
        else:
            filter = models.Q()
        revs = document.revisions.exclude(filter).order_by('-created')
        if revs.exists():
            rev = revs[0]

    return rev

add_introspection_rules([], ["^utils\.OverwritingFileField"])


def rev_upload_to(instance, filename):
    """Generate a path to store a file attachment."""
    # TODO: We could probably just get away with strftime formatting
    # in the 'upload_to' argument here, but this does a bit more to be
    # extra-safe with potential duplicate filenames.
    #
    # For now, the filesystem storage path will look like this:
    #
    # attachments/year/month/day/attachment_id/md5/filename
    #
    # The md5 hash here is of the full timestamp, down to the
    # microsecond, of when the path is generated.
    now = datetime.now()
    return "attachments/%(date)s/%(id)s/%(md5)s/%(filename)s" % {
        'date': now.strftime('%Y/%m/%d'),
        'id': instance.attachment.id,
        'md5': hashlib.md5(str(now)).hexdigest(),
        'filename': filename
    }


class AttachmentManager(models.Manager):

    def allow_add_attachment_by(self, user):
        """Returns whether the `user` is allowed to upload attachments.

        This is determined by a negative permission, `disallow_add_attachment`
        When the user has this permission, upload is disallowed unless it's
        a superuser or staff.
        """
        if user.is_superuser or user.is_staff:
            # Superusers and staff always allowed
            return True
        if user.has_perm('wiki.add_attachment'):
            # Explicit add permission overrides disallow
            return True
        if user.has_perm('wiki.disallow_add_attachment'):
            # Disallow generally applied via group, so per-user allow can
            # override
            return False
        return True


class DocumentAttachment(models.Model):
    """
    Intermediary between Documents and Attachments. Allows storing the
    user who attached a file to a document, and a (unique for that
    document) name for referring to the file from the document.

    """
    file = models.ForeignKey('Attachment')
    document = models.ForeignKey(Document)
    attached_by = models.ForeignKey(User, null=True)
    name = models.TextField()


class Attachment(models.Model):
    """
    An attachment which can be inserted into one or more wiki documents.

    There is no direct database-level relationship between attachments
    and documents; insertion of an attachment is handled through
    markup in the document.
    """
    class Meta(object):
        permissions = (
            ("disallow_add_attachment", "Cannot upload attachment"),
        )

    objects = AttachmentManager()

    current_revision = models.ForeignKey('AttachmentRevision', null=True,
                                         related_name='current_rev')

    # These get filled from the current revision.
    title = models.CharField(max_length=255, db_index=True)
    slug = models.CharField(max_length=255, db_index=True)

    # This is somewhat like the bookkeeping we do for Documents, but
    # is also slightly more permanent because storing this ID lets us
    # map from old MindTouch file URLs (which are based on the ID) to
    # new kuma file URLs.
    mindtouch_attachment_id = models.IntegerField(
        help_text="ID for migrated MindTouch resource",
        null=True, db_index=True)
    modified = models.DateTimeField(auto_now=True, null=True, db_index=True)

    @models.permalink
    def get_absolute_url(self):
        return ('wiki.attachment_detail', (), {'attachment_id': self.id})

    def get_file_url(self):
        uri = reverse('wiki.raw_file', kwargs={'attachment_id': self.id,
                               'filename':  self.current_revision.filename()})
        url = '%s%s%s' % (settings.PROTOCOL,
                         settings.ATTACHMENT_HOST,
                         uri)
        return url

    def attach(self, document, user, name):
        if self.id not in document.attachments.values_list('id', flat=True):
            intermediate = DocumentAttachment(file=self,
                                              document=document,
                                              attached_by=user,
                                              name=name)
            intermediate.save()

    def get_embed_html(self):
        """
        Return suitable initial HTML for embedding this file in an
        article, generated from a template.

        The template searching is from most specific to least
        specific, based on mime-type. For example, an attachment with
        mime-type 'image/png' will try to load the following
        templates, in order, and use the first one found:

        * wiki/attachments/image_png.html

        * wiki/attachments/image.html

        * wiki/attachments/generic.html
        """
        rev = self.current_revision
        env = jingo.get_env()
        t = env.select_template([
            'wiki/attachments/%s.html' % rev.mime_type.replace('/', '_'),
            'wiki/attachments/%s.html' % rev.mime_type.split('/')[0],
            'wiki/attachments/generic.html'])
        return t.render({'attachment': rev})


class AttachmentRevision(models.Model):
    """
    A revision of an attachment.
    """
    attachment = models.ForeignKey(Attachment, related_name='revisions')

    file = models.FileField(upload_to=rev_upload_to, max_length=500)

    title = models.CharField(max_length=255, null=True, db_index=True)
    slug = models.CharField(max_length=255, null=True, db_index=True)

    # This either comes from the MindTouch import or, for new files,
    # from the (as-yet-unwritten) upload view using the Python
    # mimetypes library to figure it out.
    #
    # TODO: do we want to make this an explicit set of choices? That'd
    # rule out certain types of attachments, but might be a lot safer.
    mime_type = models.CharField(max_length=255, db_index=True)

    description = models.TextField(blank=True)  # Does not allow wiki markup

    created = models.DateTimeField(default=datetime.now)
    comment = models.CharField(max_length=255, blank=True)
    creator = models.ForeignKey(User,
                                related_name='created_attachment_revisions')
    is_approved = models.BooleanField(default=True, db_index=True)

    # As with document revisions, bookkeeping for the MindTouch
    # migration.
    #
    # TODO: Do we actually need full file revision history from
    # MindTouch?
    mindtouch_old_id = models.IntegerField(
        help_text="ID for migrated MindTouch resource revision",
        null=True, db_index=True, unique=True)
    is_mindtouch_migration = models.BooleanField(
        default=False, db_index=True,
        help_text="Did this revision come from MindTouch?")

    def filename(self):
        return self.file.path.split('/')[-1]

    def save(self, *args, **kwargs):
        super(AttachmentRevision, self).save(*args, **kwargs)
        if self.is_approved and (
                not self.attachment.current_revision or
                self.attachment.current_revision.id < self.id):
            self.make_current()

    def make_current(self):
        """Make this revision the current one for the attachment."""
        self.attachment.title = self.title
        self.attachment.slug = self.slug
        self.attachment.current_revision = self
        self.attachment.save()

    def get_previous(self):
        previous_revisions = self.attachment.revisions.filter(
            is_approved=True,
            created__lt=self.created,
            ).order_by('-created')
        if len(previous_revisions):
            return previous_revisions[0]
        else:
            return None
