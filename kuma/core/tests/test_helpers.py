from datetime import datetime
from unittest import mock

import pytest
import pytz
from babel.dates import format_date, format_datetime, format_time
from django.conf import settings
from django.test import override_settings, RequestFactory, TestCase

from kuma.core.tests import KumaTestCase
from kuma.core.urlresolvers import reverse
from kuma.users.tests import UserTestCase

from ..exceptions import DateTimeFormatError
from ..templatetags.jinja_helpers import (
    assert_function,
    datetimeformat,
    in_utc,
    jsonencode,
    page_title,
    yesno,
)


def test_assert_function():
    with pytest.raises(RuntimeError) as exc:
        assert_function(False, "Message")
    assert str(exc.value) == "Failed assertion: Message"


def test_assert_function_no_message():
    with pytest.raises(RuntimeError) as exc:
        assert_function(False)
    assert str(exc.value) == "Failed assertion"


def test_assert_function_passes():
    assert assert_function(True, "Message") == ""


class TestYesNo(KumaTestCase):
    def test_yesno(self):
        assert "Yes" == yesno(True)
        assert "No" == yesno(False)
        assert "Yes" == yesno(1)
        assert "No" == yesno(0)


class TestDateTimeFormat(UserTestCase):
    def setUp(self):
        super(TestDateTimeFormat, self).setUp()
        url_ = reverse("home")
        self.context = {"request": RequestFactory().get(url_)}
        self.context["request"].LANGUAGE_CODE = "en-US"
        self.context["request"].user = self.user_model.objects.get(
            username="testuser01"
        )

    def test_today(self):
        """Expects shortdatetime, format: Today at {time}."""
        date_today = datetime.today()
        value_expected = "Today at %s" % format_time(
            date_today, format="short", locale="en_US"
        )
        value_returned = datetimeformat(self.context, date_today, output="json")
        assert value_expected == value_returned

    def test_locale(self):
        """Expects shortdatetime in French."""
        self.context["request"].LANGUAGE_CODE = "fr"
        value_test = datetime.fromordinal(733900)
        value_expected = format_datetime(value_test, format="short", locale="fr")
        value_returned = datetimeformat(self.context, value_test, output="json")
        assert value_expected == value_returned

    def test_default(self):
        """Expects shortdatetime."""
        value_test = datetime.fromordinal(733900)
        value_expected = format_datetime(value_test, format="short", locale="en_US")
        value_returned = datetimeformat(self.context, value_test, output="json")
        assert value_expected == value_returned

    def test_longdatetime(self):
        """Expects long format."""
        value_test = datetime.fromordinal(733900)
        tzvalue = pytz.timezone(settings.TIME_ZONE).localize(value_test)
        value_expected = format_datetime(tzvalue, format="long", locale="en_US")
        value_returned = datetimeformat(
            self.context, value_test, format="longdatetime", output="json"
        )
        assert value_expected == value_returned

    def test_date(self):
        """Expects date format."""
        value_test = datetime.fromordinal(733900)
        value_expected = format_date(value_test, locale="en_US")
        value_returned = datetimeformat(
            self.context, value_test, format="date", output="json"
        )
        assert value_expected == value_returned

    def test_time(self):
        """Expects time format."""
        value_test = datetime.fromordinal(733900)
        value_expected = format_time(value_test, locale="en_US")
        value_returned = datetimeformat(
            self.context, value_test, format="time", output="json"
        )
        assert value_expected == value_returned

    def test_datetime(self):
        """Expects datetime format."""
        value_test = datetime.fromordinal(733900)
        value_expected = format_datetime(value_test, locale="en_US")
        value_returned = datetimeformat(
            self.context, value_test, format="datetime", output="json"
        )
        assert value_expected == value_returned

    def test_unknown_format(self):
        """Unknown format raises DateTimeFormatError."""
        date_today = datetime.today()
        with pytest.raises(DateTimeFormatError):
            datetimeformat(self.context, date_today, format="unknown")

    @mock.patch("babel.dates.format_datetime")
    def test_broken_format(self, mocked_format_datetime):
        value_test = datetime.fromordinal(733900)
        value_english = format_datetime(value_test, locale="en_US")
        self.context["request"].LANGUAGE_CODE = "fr"
        mocked_format_datetime.side_effect = [
            # first call is returning a KeyError as if the format is broken
            KeyError,
            # second call returns the English fallback version as expected
            value_english,
        ]
        value_returned = datetimeformat(
            self.context, value_test, format="datetime", output="json"
        )
        assert value_english == value_returned

    def test_invalid_value(self):
        """Passing invalid value raises ValueError."""
        with pytest.raises(ValueError):
            datetimeformat(self.context, "invalid")

    def test_json_helper(self):
        assert "false" == jsonencode(False)
        assert '{"foo": "bar"}' == jsonencode({"foo": "bar"})

    def test_user_timezone(self):
        """Shows time in user timezone."""
        value_test = datetime.fromordinal(733900)
        # Choose user with non default timezone
        user = self.user_model.objects.get(username="admin")
        self.context["request"].user = user

        # Convert tzvalue to user timezone
        default_tz = pytz.timezone(settings.TIME_ZONE)
        user_tz = pytz.timezone(user.timezone)
        tzvalue = default_tz.localize(value_test)
        tzvalue = user_tz.normalize(tzvalue.astimezone(user_tz))

        value_expected = format_datetime(tzvalue, format="long", locale="en_US")
        value_returned = datetimeformat(
            self.context, value_test, format="longdatetime", output="json"
        )
        assert value_expected == value_returned


class TestInUtc(KumaTestCase):
    """Test the in_utc datetime filter."""

    def test_utc(self):
        """Assert a time in UTC remains in UTC."""
        dt = datetime(2016, 3, 10, 16, 12, tzinfo=pytz.utc)
        out = in_utc(dt)
        assert out == dt

    def test_aware(self):
        """Assert a time in a different time zone is converted to UTC."""
        hour = 10
        dt = datetime(2016, 3, 10, hour, 14)
        dt = pytz.timezone("US/Central").localize(dt)
        out = in_utc(dt)
        assert out == datetime(2016, 3, 10, hour + 6, 14, tzinfo=pytz.utc)

    @override_settings(TIME_ZONE="US/Pacific")
    def test_naive(self):
        """Assert that naïve datetimes are first converted to system time."""
        hour = 8
        dt = datetime(2016, 3, 10, hour, 8)
        out = in_utc(dt)
        assert out == datetime(2016, 3, 10, hour + 8, 8, tzinfo=pytz.utc)


class TestPageTitle(TestCase):
    def test_ascii(self):
        assert page_title("title") == "title | MDN"

    def test_xss(self):
        pt = page_title("</title><Img src=x onerror=alert(1)>")
        assert pt == "&lt;/title&gt;&lt;Img src=x onerror=alert(1)&gt; | MDN"
