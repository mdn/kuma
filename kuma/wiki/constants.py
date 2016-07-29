import re

import bleach
from django.conf import settings
from django.utils.translation import ugettext_lazy as _


ALLOWED_TAGS = bleach.ALLOWED_TAGS + [
    'div', 'span', 'p', 'br', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'pre', 'code', 'cite',
    'dl', 'dt', 'dd', 'small', 'sub', 'sup', 'u', 'strike', 'samp', 'abbr',
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
    'progress', 'audio', 'video', 'details', 'summary', 'datagrid', 'datalist',
    'table', 'address', 'font',
    'bdi', 'bdo', 'del', 'ins', 'kbd', 'samp', 'var',
    'ruby', 'rp', 'rt', 'q',
    # MathML
    'math', 'maction', 'menclose', 'merror', 'mfenced', 'mfrac', 'mglyph',
    'mi', 'mlabeledtr', 'mmultiscripts', 'mn', 'mo', 'mover', 'mpadded',
    'mphantom', 'mroot', 'mrow', 'ms', 'mspace', 'msqrt', 'mstyle',
    'msub', 'msup', 'msubsup', 'mtable', 'mtd', 'mtext', 'mtr', 'munder',
    'munderover', 'none', 'mprescripts', 'semantics', 'annotation',
    'annotation-xml',
]
ALLOWED_ATTRIBUTES = bleach.ALLOWED_ATTRIBUTES

ALLOWED_ATTRIBUTES['*'] = ['lang']
# Note: <iframe> is allowed, but src="" is pre-filtered before bleach
ALLOWED_ATTRIBUTES['iframe'] = ['id', 'src', 'sandbox', 'seamless',
                                'frameborder', 'width', 'height', 'class']
ALLOWED_ATTRIBUTES['p'] = ['style', 'class', 'id', 'align', 'lang', 'dir']
ALLOWED_ATTRIBUTES['span'] = ['style', 'class', 'id', 'title', 'lang', 'dir']
ALLOWED_ATTRIBUTES['abbr'] = ['style', 'class', 'id', 'title', 'lang', 'dir']
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
ALLOWED_ATTRIBUTES['details'] = ['open']
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
ALLOWED_ATTRIBUTES['li'] += ['data-default-state']
ALLOWED_ATTRIBUTES['time'] += ['datetime']
ALLOWED_ATTRIBUTES['ins'] = ['datetime']
ALLOWED_ATTRIBUTES['del'] = ['datetime']
ALLOWED_ATTRIBUTES['meter'] += ['max', 'min', 'value', 'low', 'high', 'optimum',
                                'form']
# MathML
ALLOWED_ATTRIBUTES.update(dict((x, ['encoding', 'src']) for x in (
    'annotation', 'annotation-xml')))
ALLOWED_ATTRIBUTES.update(
    dict((x,
          ['href', 'mathbackground', 'mathcolor',
           'id', 'class', 'style']) for x in ('math', 'maction', 'menclose',
                                              'merror', 'mfenced', 'mfrac', 'mglyph',
                                              'mi', 'mlabeledtr', 'mmultiscripts',
                                              'mn', 'mo', 'mover', 'mpadded',
                                              'mphantom', 'mroot', 'mrow', 'ms',
                                              'mspace', 'msqrt', 'mstyle',
                                              'msub', 'msup', 'msubsup', 'mtable',
                                              'mtd', 'mtext', 'mtr', 'munder',
                                              'munderover', 'none', 'mprescripts')))
ALLOWED_ATTRIBUTES['math'] += [
    'display', 'dir', 'selection', 'notation',
    'close', 'open', 'separators', 'bevelled', 'denomalign', 'linethickness',
    'numalign', 'largeop', 'maxsize', 'minsize', 'movablelimits', 'rspace',
    'separator', 'stretchy', 'symmetric', 'depth', 'lquote', 'rquote', 'align',
    'columnlines', 'frame', 'rowalign', 'rowspacing', 'rowspan', 'columnspan',
    'accent', 'accentunder', 'dir', 'mathsize', 'mathvariant',
    'subscriptshift', 'supscriptshift', 'scriptlevel', 'displaystyle',
    'scriptsizemultiplier', 'scriptminsize', 'altimg', 'altimg-width',
    'altimg-height', 'altimg-valign', 'alttext']
ALLOWED_ATTRIBUTES['maction'] += ['actiontype', 'selection']
ALLOWED_ATTRIBUTES['menclose'] += ['notation']
ALLOWED_ATTRIBUTES['mfenced'] += ['close', 'open', 'separators']
ALLOWED_ATTRIBUTES['mfrac'] += ['bevelled', 'denomalign', 'linethickness',
                                'numalign']
ALLOWED_ATTRIBUTES['mi'] += ['dir', 'mathsize', 'mathvariant']
ALLOWED_ATTRIBUTES['mn'] += ['dir', 'mathsize', 'mathvariant']
ALLOWED_ATTRIBUTES['mmultiscripts'] += ['subscriptshift', 'superscriptshift']
ALLOWED_ATTRIBUTES['mo'] += ['largeop', 'lspace', 'maxsize', 'minsize',
                             'movablelimits', 'rspace', 'separator',
                             'stretchy', 'symmetric', 'accent',
                             'dir', 'mathsize', 'mathvariant']
ALLOWED_ATTRIBUTES['mover'] += ['accent']
ALLOWED_ATTRIBUTES['mpadded'] += ['lspace', 'voffset', 'depth']
ALLOWED_ATTRIBUTES['mrow'] += ['dir']
ALLOWED_ATTRIBUTES['ms'] += ['lquote', 'rquote', 'dir', 'mathsize',
                             'mathvariant']
ALLOWED_ATTRIBUTES['mspace'] += ['depth', 'height', 'width']
ALLOWED_ATTRIBUTES['mstyle'] += [
    'display', 'dir', 'selection', 'notation',
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
    '-moz-transition-timing-function', '-webkit-transition-timing-function',
    '-o-transition-timing-function', 'color', 'display', 'position',
    'outline-color', 'outline', 'outline-offset', 'box-shadow',
    '-moz-box-shadow', '-webkit-box-shadow', '-o-box-shadow',
    'linear-gradient', '-moz-linear-gradient', '-webkit-linear-gradient',
    'radial-gradient', '-moz-radial-gradient', '-webkit-radial-gradient',
    'text-decoration-style', '-moz-text-decoration-style', 'text-decoration',
    'direction', 'white-space', 'unicode-bidi', 'word-wrap'
]

DIFF_WRAP_COLUMN = 65
TEMPLATE_TITLE_PREFIX = 'Template:'
DOCUMENTS_PER_PAGE = 100
KUMASCRIPT_TIMEOUT_ERROR = [
    {"level": "error",
     "message": "Request to Kumascript service timed out",
     "args": ["TimeoutError"]}
]

# TODO: Put this under the control of Constance / Waffle?
# Flags used to signify revisions in need of review
REVIEW_FLAG_TAGS = (
    ('technical', _('Technical - code samples, APIs, or technologies')),
    ('editorial', _('Editorial - prose, grammar, or content')),
)
REVIEW_FLAG_TAGS_DEFAULT = ['technical', 'editorial']

LOCALIZATION_FLAG_TAGS = (
    ('inprogress', _('Localization in progress - not completely translated yet.')),
)

# TODO: This is info derived from urls.py, but unsure how to DRY it
RESERVED_SLUGS = (
    r'ckeditor_config\.js$',
    r'watch-ready-for-review$',
    r'unwatch-ready-for-review$',
    r'watch-approved$',
    r'unwatch-approved$',
    r'\.json$',
    r'new$',
    r'all$',
    r'templates$',
    r'preview-wiki-content$',
    r'category/\d+$',
    r'needs-review/?[^/]+$',
    r'needs-review/?',
    r'feeds/[^/]+/all/?',
    r'feeds/[^/]+/needs-review/[^/]+$',
    r'feeds/[^/]+/needs-review/?',
    r'tag/[^/]+'
)
RESERVED_SLUGS_RES = [re.compile(pattern) for pattern in RESERVED_SLUGS]
SLUG_CLEANSING_RE = re.compile(r'^\/?(([A-z-]+)?\/?docs\/)?')
# ?, whitespace, percentage, quote disallowed in slugs altogether
INVALID_DOC_SLUG_CHARS_RE = re.compile(r"""[\s'"%%\?\$]+""")
INVALID_REV_SLUG_CHARS_RE = re.compile(r"""[\s\?\/%%]+""")
DOCUMENT_PATH_RE = re.compile(r'[^\$]+')

# how a redirect looks as rendered HTML
REDIRECT_HTML = 'REDIRECT <a class="redirect"'
REDIRECT_CONTENT = 'REDIRECT <a class="redirect" href="%(href)s">%(title)s</a>'

DOCUMENT_LAST_MODIFIED_CACHE_KEY_TMPL = u'kuma:document-last-modified:%s'

DEKI_FILE_URL = re.compile(r'@api/deki/files/(?P<file_id>\d+)/=')
KUMA_FILE_URL = re.compile(r'%s%s/files/(?P<file_id>\d+)/' %
                           (re.escape(settings.PROTOCOL),
                            re.escape(settings.ATTACHMENT_HOST)))

SPAM_EXEMPTED_FLAG = 'wiki_spam_exempted'
SPAM_TRAINING_FLAG = 'wiki_spam_training'
SPAM_SUBMISSION_REVISION_FIELDS = [
    'title',
    'slug',
    'summary',
    'content',
    'comment',
    'tags',
    'keywords',
]
SPAM_OTHER_HEADERS = (  # Header to send that don't start with HTTP
    'REMOTE_ADDR',
    'REQUEST_URI',
    'DOCUMENT_URI',
)

CODE_SAMPLE_MACROS = [
    'LiveSampleURL',
    'EmbedDistLiveSample',
    'EmbedLiveSample',
    'LiveSampleLink',
    'FXOSUXLiveSampleEmbed',
]

DEV_DOC_REQUEST_FORM = 'https://bugzilla.mozilla.org/form.doc'
