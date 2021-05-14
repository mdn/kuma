from babel.numbers import format_currency
from django_jinja import library


@library.filter
def money(value, currency="USD"):
    return format_currency(value, currency, locale="en")
