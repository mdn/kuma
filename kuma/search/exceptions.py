from django.utils.encoding import force_text
from rest_framework import status
from rest_framework.exceptions import APIException


def _force_text_recursive(data):
    """
    Descend into a nested data structure, forcing any
    lazy translation strings into plain text.
    """
    if isinstance(data, list):
        return [
            _force_text_recursive(item) for item in data
        ]
    elif isinstance(data, dict):
        return dict([
            (key, _force_text_recursive(value))
            for key, value in data.items()
        ])
    return force_text(data)


class ValidationError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, detail):
        # For validation errors the 'detail' key is always required.
        # The details should always be coerced to a list if not already.
        if not isinstance(detail, dict) and not isinstance(detail, list):
            detail = [detail]
        self.detail = _force_text_recursive(detail)

    def __str__(self):
        return self.detail
