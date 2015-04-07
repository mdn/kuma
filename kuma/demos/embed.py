"""
Quick and mostly dirty model utils for embedded media fields in Django with Jinja2.

Currently just YouTube and Vimeo video.

Blame lorchard@mozilla.com for this mess.
see also: https://gist.github.com/796214

@@TODO:liberate
@@TODO: Allow definition of default iframe width/height in VideoEmbedURLField
@@TODO: Add more video services / find a safe way to use embed.ly?
"""
import re

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _
from jinja2.utils import Markup

YOUTUBE_URL_RE = re.compile("""
    ^ # start
    http:// # schema
    (?:www\\.)? # optional www.
    youtube\\.com/watch\? # domain + path
    (?:.*?&)*? # optional leading params (except v=)
    v=(?P<id>\w+) # v=<video id>
    (&.*)? # optional trailing params
    $ # end
""", re.VERBOSE)

YOUTUBE_EMBED_URL = 'http://www.youtube.com/embed/%(id)s'

VIMEO_URL_RE = re.compile("""
    ^ # start
    http:// # schema
    (?:www\\.)? # optional www.
    vimeo\\.com/ # domain + path
    (?P<id>\d+) # <video id>
    (\?.*)? # optional params
    $ # end
""", re.VERBOSE)

VIMEO_EMBED_URL = 'http://player.vimeo.com/video/%(id)s'

EMBED_PATTERNS = (
    (YOUTUBE_URL_RE, YOUTUBE_EMBED_URL),
    (VIMEO_URL_RE, VIMEO_EMBED_URL)
)

EMBED_CODE = (
    u'<iframe type="text/html" width="%(width)d" height="%(height)d" '
    u'    src="%(url)s" frameborder="0"></iframe>'
)
DEFAULT_PARAMS = {'width': 480, 'height': 360}


def build_video_embed(url, **kwargs):
    for regex, embed_url in EMBED_PATTERNS:
        match = regex.match(url)
        if match:
            params = dict(DEFAULT_PARAMS)
            params.update(kwargs)
            params['url'] = embed_url % match.groupdict()
            return EMBED_CODE % params
    return None


class VideoEmbedURL(object):
    """Proxy for access on a VideoEmbedURLField, offers embed_html property"""

    def __init__(self, instance, field, value):
        self.instance = instance
        self.field = field
        self.value = value

    def __unicode__(self):
        return self.value

    @property
    def embed_html(self):
        return Markup(build_video_embed(self.value))


class VideoEmbedURLDescriptor(object):
    """
    Transforms a plain URL into VideoEmbedURL on field access
    see also: django.db.models.fields.files.FileField
    """
    def __init__(self, field):
        self.field = field

    def __set__(self, instance, value):
        instance.__dict__[self.field.name] = value

    def __get__(self, instance=None, owner=None):
        if instance is None:
            raise AttributeError(
                "The '%s' attribute can only be accessed from %s instances."
                % (self.field.name, owner.__name__))

        veurl = instance.__dict__[self.field.name]

        if isinstance(veurl, basestring) or veurl is None:
            attr = self.field.attr_class(instance, self.field, veurl)
            instance.__dict__[self.field.name] = attr

        elif isinstance(veurl, VideoEmbedURL) and not hasattr(veurl, 'field'):
            veurl.instance = instance
            veurl.field = self.field

        out = instance.__dict__[self.field.name]
        if not out or not out.value:
            return None
        return out


class VideoEmbedURLField(models.URLField):
    """
    URL field with the magical ability to enable media embedding via the
    embed_html property
    """
    attr_class = VideoEmbedURL
    descriptor_class = VideoEmbedURLDescriptor

    def validate(self, value, model_instance):
        super(VideoEmbedURLField, self).validate(value, model_instance)
        if not build_video_embed(value):
            raise ValidationError(_('Not an URL from a supported video service'))

    def get_prep_value(self, field_value):
        "Returns field's value prepared for saving into a database."
        if field_value is None or field_value.value is None:
            return ''
        return unicode(field_value)

    def contribute_to_class(self, cls, name):
        super(VideoEmbedURLField, self).contribute_to_class(cls, name)
        setattr(cls, self.name, self.descriptor_class(self))
