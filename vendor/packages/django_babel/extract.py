# -*- coding: utf-8 -*-
try:
    from django.template import Lexer, TOKEN_TEXT, TOKEN_VAR, TOKEN_BLOCK
except ImportError:
    # Django 1.8 moved most stuff to .base
    from django.template.base import Lexer, TOKEN_TEXT, TOKEN_VAR, TOKEN_BLOCK

from django.utils.translation.trans_real import (
    inline_re, block_re, endblock_re, plural_re, constant_re)
from django.utils.encoding import smart_text


def extract_django(fileobj, keywords, comment_tags, options):
    """Extract messages from Django template files.

    :param fileobj: the file-like object the messages should be extracted from
    :param keywords: a list of keywords (i.e. function names) that should
                     be recognized as translation functions
    :param comment_tags: a list of translator tags to search for and
                         include in the results
    :param options: a dictionary of additional options (optional)
    :return: an iterator over ``(lineno, funcname, message, comments)``
             tuples
    :rtype: ``iterator``
    """
    intrans = False
    inplural = False
    singular = []
    plural = []
    lineno = 1

    encoding = options.get('encoding', 'utf8')
    text = fileobj.read().decode(encoding)

    for t in Lexer(text, None).tokenize():
        lineno += t.contents.count('\n')
        if intrans:
            if t.token_type == TOKEN_BLOCK:
                endbmatch = endblock_re.match(t.contents)
                pluralmatch = plural_re.match(t.contents)
                if endbmatch:
                    if inplural:
                        yield (
                            lineno,
                            'ngettext',
                            (smart_text(u''.join(singular)),
                             smart_text(u''.join(plural))),
                            [])
                    else:
                        yield (
                            lineno,
                            None,
                            smart_text(u''.join(singular)),
                            [])

                    intrans = False
                    inplural = False
                    singular = []
                    plural = []
                elif pluralmatch:
                    inplural = True
                else:
                    raise SyntaxError('Translation blocks must not include '
                                      'other block tags: %s' % t.contents)
            elif t.token_type == TOKEN_VAR:
                if inplural:
                    plural.append('%%(%s)s' % t.contents)
                else:
                    singular.append('%%(%s)s' % t.contents)
            elif t.token_type == TOKEN_TEXT:
                if inplural:
                    plural.append(t.contents)
                else:
                    singular.append(t.contents)
        else:
            if t.token_type == TOKEN_BLOCK:
                imatch = inline_re.match(t.contents)
                bmatch = block_re.match(t.contents)
                cmatches = constant_re.findall(t.contents)
                if imatch:
                    g = imatch.group(1)
                    if g[0] == '"':
                        g = g.strip('"')
                    elif g[0] == "'":
                        g = g.strip("'")
                    yield lineno, None, smart_text(g), []
                elif bmatch:
                    for fmatch in constant_re.findall(t.contents):
                        yield lineno, None, smart_text(fmatch), []
                    intrans = True
                    inplural = False
                    singular = []
                    plural = []
                elif cmatches:
                    for cmatch in cmatches:
                        yield lineno, None, smart_text(cmatch), []
            elif t.token_type == TOKEN_VAR:
                parts = t.contents.split('|')
                cmatch = constant_re.match(parts[0])
                if cmatch:
                    yield lineno, None, smart_text(cmatch.group(1)), []
                for p in parts[1:]:
                    if p.find(':_(') >= 0:
                        p1 = p.split(':', 1)[1]
                        if p1[0] == '_':
                            p1 = p1[1:]
                        if p1[0] == '(':
                            p1 = p1.strip('()')
                        if p1[0] == "'":
                            p1 = p1.strip("'")
                        elif p1[0] == '"':
                            p1 = p1.strip('"')
                        yield lineno, None, smart_text(p1), []
