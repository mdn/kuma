import calendar
import datetime


MONTH_TAG_NAMES = [
    'january',
    'february',
    'march',
    'april',
    'may',
    'june',
    'july',
    'august',
    'september',
    'october',
    'november',
    'december',
]

MONTH_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

MONTH_MAP = dict(zip(MONTH_TAG_NAMES, range(1, 13)))

MONTH_END_MAP = dict(zip(range(1, 13), MONTH_DAYS))


def challenge_tag_to_date_parts(tag):
    year, month = str(tag).split(':')[1:]
    return int(year), MONTH_MAP[month]


def challenge_tag_to_end_date(tag):
    """
    Given a dev derby challenge tag, return the date on which the
    challenge ends.

    """
    year, month = challenge_tag_to_date_parts(tag)
    if month == 2 and calendar.isleap(year):
        return datetime.date(year, month, 29)
    return datetime.date(year, month, MONTH_END_MAP[month])


def challenge_closed(tags):
    if not tags:
        return True
    return datetime.date.today() > max(map(challenge_tag_to_end_date, tags))
