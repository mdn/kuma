import time
from babel import localedata
from babel.dates import format_date, format_time

from django.conf import settings
import jinja2
from jingo import register

from sumo_locales import LOCALES

@register.function
@jinja2.contextfunction
def datetimeformat(context, value):
    locale = LOCALES[context['request'].locale].internal
    if not localedata.exists(locale):
        locale = LOCALES[settings.LANGUAGE_CODE].internal

    # If within a day, 24 * 60 * 60 = 86400s
    if abs(time.time() - time.mktime(value.timetuple())) < 86400:
        return format_time(value, locale=locale)
    else:
        return format_date(value, locale=locale)
