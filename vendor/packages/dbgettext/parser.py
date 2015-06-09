from django.conf import settings
from .registry import registry
import re

SENTENCE_RE = getattr(settings, 'DBGETTEXT_SENTENCE_RE', re.compile(r'^(.*?\S[\!\?\.])(\s+)(\S+.*)$', re.DOTALL))

class Token(object):
    """ A categorised chunk of HTML content """

    NEVER_TRANSLATE = 0   # e.g. comments, javascript, etc.
    MAYBE_TRANSLATE = 1   # e.g. whitespace -- surrounded by text vs on own 
    ALWAYS_TRANSLATE = 2  # e.g. text

    def __init__(self, type, raw):
        self.type = type
        self.raw = raw

    def is_translatable(self):
        if self.type == 'text':
            return Token.ALWAYS_TRANSLATE
        elif self.type == 'whitespace':
            if self.raw.find('\r') >= 0: # carriage-returns forbidden
                return Token.NEVER_TRANSLATE
            else:
                return Token.MAYBE_TRANSLATE
        else:
            return Token.NEVER_TRANSLATE

    def get_raw(self):
        """ Hook to allow subclasses to perform inner translation """
        return self.raw

    def get_gettext(self):
        """ Return list of inner translatable strings """
        return []


def flatten_token_list(token_list):
    """ Recursively flattens list of tokens.

    Allows scanner callbacks to return lists of tokens.
    """

    flat_list = []
    for token in token_list:
        if isinstance(token, list):
            flat_list += flatten_token_list(token)
        else:
            flat_list.append(token)
    return flat_list


def parsed_gettext(obj, attribute, export=False):
    """ Extracts translatable strings from parsable content
    
    Returns original content with ugettext applied to translatable parts.

    If export is True, returns a list of translatable strings only.

    """

    options = registry._registry[type(obj)]
    content = getattr(obj, attribute)
    try:
        lexicon = options.parsed_attributes[attribute]
    except:
        raise Exception("Invalid lexicon configuration in parsed_attributes")

    from django.utils.translation import ugettext as _
    # lazy / string_concat don't seem to work how I want...

    scanner = re.Scanner(lexicon(options), re.DOTALL)
    tokens, remainder = scanner.scan(content)
    tokens = flatten_token_list(tokens)

    gettext = []
    output = []
    current_string = []

    def token_list_should_be_translated(token_list):
        """ True if any token is ALWAYS_TRANSLATE """
        for t in token_list:
            if t.is_translatable() == Token.ALWAYS_TRANSLATE:
                return True
        return False

    def gettext_from_token_list(token_list):
        """ Process token list into format string, parameters and remainder """
        format, params, remainder, inner_gettext = '', {}, '', []
        # remove any trailing whitespace
        while token_list[-1].type == 'whitespace':
            remainder = token_list.pop().raw + remainder
        for t in token_list:
            if hasattr(t, 'get_key'): 
                format += '%%(%s)s' % t.get_key()
                params[t.get_key()] = t.get_raw()
            else:
                format += t.get_raw().replace('%', '%%')
            inner_gettext += t.get_gettext()
        return format, params, remainder, inner_gettext

    for t in tokens + [Token('empty', '',)]:
        if current_string:
            # in the middle of building a translatable string
            if t.is_translatable():
                current_string.append(t)
            else:
                # end of translatable token sequence, check for text content
                if token_list_should_be_translated(current_string):
                    format, params, trailing_whitespace, inner_gettext = \
                        gettext_from_token_list(current_string)
                    gettext.append(format)
                    gettext += inner_gettext
                    try:
                        output.append(_(format) % params)
                    except KeyError:
                        # translator edited placeholder names? Fallback:
                        output.append(format % params)
                    output.append(trailing_whitespace)
                else:
                    # should not be translated, raw output only
                    output.append(''.join([x.raw for x in current_string]))
                # empty for next time:
                current_string = []
                # don't forget current token also:
                output.append(t.raw)
        else:
            # should we start a new translatable string?
            if t.is_translatable() and t.type != 'whitespace':
                current_string.append(t)
            else:
                output.append(t.raw)             

    if export:
        if remainder:
            raise Exception('scanner got stuck on: "%s"(...)' % remainder[:10])
        return gettext
    else:
        return ''.join(output)
