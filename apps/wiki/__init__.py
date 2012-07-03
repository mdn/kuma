DIFF_WRAP_COLUMN = 65
TEMPLATE_TITLE_PREFIX = 'Template:'
DOCUMENTS_PER_PAGE = 100
KUMASCRIPT_TIMEOUT_ERROR = [
    {"level": "error",
     "message": "Request to Kumascript service timed out",
     "args": ["TimeoutError"]}
]


class ReadOnlyException(Exception):
    """
    A special exception to signal the wiki is read-only
    """
    pass
