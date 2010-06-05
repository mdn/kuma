import re

MARKUP_PATTERNS = (
    # Turns [external|link] into [external link] but not [[internal|links]]
    (r'(?!\[\[)\[(?P<href>[^\]]*?)\|(?P<name>[^\]]*?)\]',
     '[\g<href> \g<name>]'),
    (r'===(?P<underlined>.*?)===', '<u>\g<underlined></u>'),
    (r'__(?P<bold>.*?)__', "'''\g<bold>'''"),
    (r'\(\((?P<href>[^)]*?)\|(?P<name>[^)]*?)\)\)', '[[\g<href>|\g<name>]]'),
    (r'\(\((?P<href>.*?)\)\)', '[[\g<href>]]'),
    (r'^!!!!!!\s*(?P<heading>.*?)$', '====== \g<heading> ======'),
    (r'^!!!!!\s*(?P<heading>.*?)$', '===== \g<heading> ====='),
    (r'^!!!!\s*(?P<heading>.*?)$', '==== \g<heading> ===='),
    (r'^!!!\s*(?P<heading>.*?)$', '=== \g<heading> ==='),
    (r'^!!\s*(?P<heading>.*?)$', '== \g<heading> =='),
    (r'^!\s*(?P<heading>.*?)$', '= \g<heading> ='),
    (r'^---(?P<separator>[ \n])', '----\g<separator>'),
    (r'\{CODE\(\)\}(?P<codetext>.*?)\{CODE\}', '<code>\g<codetext></code>'),
    (r'%{3,}', '<br/>'),
    (r'^\^(?P<quotedtext>.*?)\^\s*$',
     '<blockquote>\g<quotedtext></blockquote>'),
    (r'\{maketoc\}', ' '),
    (r'\{ANAME.*?\}', ' '),
    (r'\{[a-zA-Z]+.*?\}', ' '),
    (r'~/?np~', ' '),
    (r'~/?(h|t)c~', ' '),
)

compiled_patterns = []
for pattern in MARKUP_PATTERNS:
    p = [re.compile(pattern[0], re.MULTILINE | re.DOTALL)]
    p.append(pattern[1])

    compiled_patterns.append(p)


class TikiMarkupConverter(object):
    """
    Converter for Tiki syntax to MediaWiki syntax.
    """

    def convert(self, text):
        for p in compiled_patterns:
            text = p[0].sub(p[1], text)
        return text
