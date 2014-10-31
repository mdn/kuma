from dbgettext.parser import Token, SENTENCE_RE
from django.conf import settings

class Tag(Token):
    """ An opening/closing/empty HTML tag """

    gettext_inline_tags = getattr(settings, 'DBGETTEXT_INLINE_HTML_TAGS', 
                                   ('b','i','u','em','strong',))

    def __init__(self, type, raw, name, attributes=None):
        super(Tag, self).__init__(type, raw)
        self.name = name
        self.attributes = attributes

    def is_translatable(self):
        if self.name.lower() in Tag.gettext_inline_tags:
            return Token.MAYBE_TRANSLATE
        else:
            return Token.NEVER_TRANSLATE


def lexicon(options):
    def ignore(scanner, token):
        return Token('ignore', token)

    def open_tag(scanner, token):
        return Tag('open', token, scanner.match.groups()[0])

    def close_tag(scanner, token):
        return Tag('close', token, scanner.match.groups()[0])

    def empty_tag(scanner, token):
        return Tag('empty', token, scanner.match.groups()[0])

    def open_tag_with_attributes(scanner, token):
        return Tag(*(('open', token,) + scanner.match.groups()[:2]))

    def empty_tag_with_attributes(scanner, token):
        return Tag(*(('empty', token,) + scanner.match.groups()[:2]))

    def text(scanner, token):
        if getattr(settings, 'DBGETTEXT_SPLIT_SENTENCES', True):
            text = token
            tokens = []
            while True:
                m = SENTENCE_RE.match(text)
                if m:
                    tokens.append(Token('text',m.groups()[0]))
                    tokens.append(Token('whitespace',m.groups()[1]))
                    text = m.groups()[2]
                    if text:
                        tokens.append(Token('sentence_separator',''))
                else:
                    break
            if text:
                tokens.append(Token('text', text))
            return tokens
        else:
            return Token('text', token)

    def whitespace(scanner, token):
        return Token('whitespace', token)

    ignored = [
        (r'<!--.*?-->', ignore),
        (r'<script.*?/script>', ignore),
        (r'\r', ignore), # forbidden in gettext, must split on these
    ]

    custom = getattr(options, 'custom_lexicon_rules', [])

    tags = [
        (r'<\s*/\s*([^>]*?)\s*>', close_tag),
        (r'<\s*([^>]*?)\s*/\s*>', empty_tag),
        (r'<\s*([a-zA-Z]+)\s+([^\s>][^>]*?)\s*>', 
         open_tag_with_attributes),
        (r'<\s*([a-zA-Z]+)\s+([^\s>][^>]*?)\s*/\s*>', 
         empty_tag_with_attributes),
        (r'<\s*([^>]*?)\s*>', open_tag),
    ]

    whitespace = [
        (r'\s+', whitespace),
        (r'&nbsp;', whitespace),
    ]

    text = [
        (r'[^\r<>]*[^\s<>]', text),
    ]
    
    lexicon = ignored + custom + tags + whitespace + text

    return lexicon

