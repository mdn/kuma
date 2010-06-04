import re

MARKUP_PATTERNS = (
    (r'===(?P<underlined>.*?)===', '<u>\g<underlined></u>'),
    (r'__(?P<bold>.*?)__', "'''\g<bold>'''"),
    (r'\(\((?P<href>[^)]*?)\|(?P<name>[^)]*?)\)\)', '[[\g<href>|\g<name>]]'),
    (r'\(\((?P<href>.*?)\)\)', '[[\g<href>]]'),
    (r'^!!!!!!\s(?P<heading>.*?)$', '====== \g<heading> ======'),
    (r'^!!!!!\s(?P<heading>.*?)$', '===== \g<heading> ====='),
    (r'^!!!!\s(?P<heading>.*?)$', '==== \g<heading> ===='),
    (r'^!!!\s(?P<heading>.*?)$', '=== \g<heading> ==='),
    (r'^!!\s(?P<heading>.*?)$', '== \g<heading> =='),
    (r'^!\s(?P<heading>.*?)$', '= \g<heading> ='),
    (r'^---(?P<separator>[ \n])', '----\g<separator>'),
    (r'\{CODE\(\)\}(?P<codetext>.*?)\{CODE\}', '<code>\g<codetext></code>'),
    (r'\{maketoc\}',),
    (r'\{ANAME.*?ANAME\}',),
    (r'\{[a-zA-Z]+.*?\}',),
    (r'%{3,}', '<br/>'),
    (r'~/?np~',),
    (r'~/?(h|t)c~',),
    (r'^\^(?P<quotedtext>.*?)\^\s*$',
     '<blockquote>\g<quotedtext></blockquote>'),
)


class TikiMarkupConverter(object):
    """
    Converter for Tiki syntax to MediaWiki syntax.
    """

    compiled_patterns = []

    def __init__(self):
        for pattern in MARKUP_PATTERNS:
            p = [re.compile(pattern[0], re.MULTILINE | re.DOTALL)]
            if len(pattern) > 1:
                p.append(pattern[1])
            else:
                p.append(' ')

            self.compiled_patterns.append(p)

    def convert(self, text):
        for p in self.compiled_patterns:
            text = p[0].sub(p[1], text)
        return text
