# see also: http://github.com/tav/scripts/raw/master/validate_jsonp.py
# Placed into the Public Domain by tav <tav@espians.com>

"""Validate Javascript Identifiers for use as JSON-P callback parameters."""


import re
from unicodedata import category


# ------------------------------------------------------------------------------
# javascript identifier unicode categories and "exceptional" chars
# ------------------------------------------------------------------------------

valid_jsid_categories_start = frozenset(["Lu", "Ll", "Lt", "Lm", "Lo", "Nl"])

valid_jsid_categories = frozenset(
    ["Lu", "Ll", "Lt", "Lm", "Lo", "Nl", "Mn", "Mc", "Nd", "Pc"]
)

valid_jsid_chars = ("$", "_")

# ------------------------------------------------------------------------------
# regex to find array[index] patterns
# ------------------------------------------------------------------------------

array_index_regex = re.compile(r"\[[0-9]+\]$")

has_valid_array_index = array_index_regex.search
replace_array_index = array_index_regex.sub

# ------------------------------------------------------------------------------
# javascript reserved words -- including keywords and null/boolean literals
# ------------------------------------------------------------------------------

is_reserved_js_word = frozenset(
    [
        "abstract",
        "boolean",
        "break",
        "byte",
        "case",
        "catch",
        "char",
        "class",
        "const",
        "continue",
        "debugger",
        "default",
        "delete",
        "do",
        "double",
        "else",
        "enum",
        "export",
        "extends",
        "false",
        "final",
        "finally",
        "float",
        "for",
        "function",
        "goto",
        "if",
        "implements",
        "import",
        "in",
        "instanceof",
        "int",
        "interface",
        "long",
        "native",
        "new",
        "null",
        "package",
        "private",
        "protected",
        "public",
        "return",
        "short",
        "static",
        "super",
        "switch",
        "synchronized",
        "this",
        "throw",
        "throws",
        "transient",
        "true",
        "try",
        "typeof",
        "var",
        "void",
        "volatile",
        "while",
        "with",
        # potentially reserved in a future version of the ES5 standard
        # 'let', 'yield'
    ]
).__contains__

# ------------------------------------------------------------------------------
# the core validation functions
# ------------------------------------------------------------------------------


def valid_javascript_identifier(identifier, escape="\\u", ucd_cat=category):
    """Return whether the given ``id`` is a valid Javascript identifier."""

    if not identifier:
        return False

    if not isinstance(identifier, str):
        try:
            identifier = str(identifier, "utf-8")
        except UnicodeDecodeError:
            return False

    if escape in identifier:

        new = []
        add_char = new.append
        split_id = identifier.split(escape)
        add_char(split_id.pop(0))

        for segment in split_id:
            if len(segment) < 4:
                return False
            try:
                add_char(chr(int("0x" + segment[:4], 16)))
            except Exception:
                return False
            add_char(segment[4:])

        identifier = "".join(new)

    if is_reserved_js_word(identifier):
        return False

    first_char = identifier[0]

    if not (
        (first_char in valid_jsid_chars)
        or (ucd_cat(first_char) in valid_jsid_categories_start)
    ):
        return False

    for char in identifier[1:]:
        if not ((char in valid_jsid_chars) or (ucd_cat(char) in valid_jsid_categories)):
            return False

    return True


def valid_jsonp_callback_value(value):
    """Return whether the given ``value`` can be used as a JSON-P callback."""

    for identifier in value.split("."):
        while "[" in identifier:
            if not has_valid_array_index(identifier):
                return False
            identifier = replace_array_index("", identifier)
        if not valid_javascript_identifier(identifier):
            return False

    return True
