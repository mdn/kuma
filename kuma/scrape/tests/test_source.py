"""Tests for the Source class."""


from unittest import mock

import pytest

from kuma.scrape.sources import Source

from . import mock_requester, mock_storage


class FakeSource(Source):
    """A Fake source for testing shared Source functionality."""

    PARAM_NAME = "name"

    OPTIONS = {
        "pressed": ("bool", False),
        "length": ("int", 0),
        "unbounded": ("int_all", 0),
        "flavor": ("text", ""),
    }


def test_init_param():
    """Omitted Source parameters are initialized to defaults."""
    source = FakeSource("param")
    assert source.name == "param"
    assert source.length == 0
    assert source.pressed is False
    assert source.unbounded == 0
    assert source.flavor == ""


@pytest.mark.parametrize(
    "option,value",
    (
        ("pressed", True),
        ("length", 1),
        ("unbounded", "all"),
        ("flavor", "curry"),
    ),
    ids=("bool", "int", "int_all", "text"),
)
def test_init_options(option, value):
    """Source parameters are initialized by name."""
    source = FakeSource("popcorn", **{option: value})
    assert source.name == "popcorn"
    assert getattr(source, option) == value


def test_init_invalid_option():
    """An invalid parameter name raises an exception."""
    with pytest.raises(Exception):
        FakeSource("param", unknown=1)


def test_merge_none():
    """An empty merge does not change the Source state."""
    source = FakeSource("merge")
    source.state = source.STATE_PREREQ
    assert source.merge_options() == {}
    assert source.state == source.STATE_PREREQ


@pytest.mark.parametrize(
    "option,lesser_value,greater_value",
    (
        ("pressed", False, True),
        ("length", 1, 2),
        ("unbounded", 2, 3),
    ),
    ids=("bool", "int", "int_all"),
)
def test_merge_less(option, lesser_value, greater_value):
    """A merge to smaller parameters keeps the current values and state."""
    source = FakeSource("merge", **{option: greater_value})
    source.state = source.STATE_PREREQ
    assert source.merge_options(**{option: lesser_value}) == {}
    assert getattr(source, option) == greater_value
    assert source.state == source.STATE_PREREQ


@pytest.mark.parametrize(
    "option,value",
    (
        ("pressed", True),
        ("length", 2),
        ("unbounded", 1),
        ("flavor", "country"),
    ),
    ids=("bool", "int", "int_all", "text"),
)
def test_merge_same(option, value):
    """A merge with the current values keeps the current state."""
    source = FakeSource("merge", **{option: value})
    source.state = source.STATE_PREREQ
    assert source.merge_options(**{option: value}) == {}
    assert getattr(source, option) == value
    assert source.state == source.STATE_PREREQ


@pytest.mark.parametrize(
    "option,lesser_value,greater_value",
    (
        ("pressed", False, True),
        ("length", 1, 2),
        ("unbounded", 2, 3),
    ),
    ids=("bool", "int", "int_all"),
)
def test_merge_upgrade(option, lesser_value, greater_value):
    """An updating merge updates the values and resets the state."""
    source = FakeSource("merge", **{option: lesser_value})
    source.state = source.STATE_PREREQ
    result = source.merge_options(**{option: greater_value})
    assert result == {option: greater_value}
    assert getattr(source, option) == greater_value
    assert source.state == source.STATE_INIT


def test_merge_more_multiple():
    """Multiple parameters can be updated in one merge call."""
    source = FakeSource("merge")
    res = source.merge_options(length=1, pressed=True, unbounded=1, flavor="salty")
    assert res == {"length": 1, "pressed": True, "unbounded": 1, "flavor": "salty"}


def test_merge_int_all():
    """For the 'int_all' parameter type, 'all' is a valid and maximum value."""
    source = FakeSource("merge")
    assert source.merge_options(unbounded="all") == {"unbounded": "all"}
    assert source.merge_options(unbounded="all") == {}


def test_merge_text():
    """For the 'text' parameter type, any non-empty change is an update."""
    source = FakeSource("merge")
    assert source.merge_options(flavor="sweet") == {"flavor": "sweet"}
    assert source.merge_options(flavor="sour") == {"flavor": "sour"}
    assert source.merge_options(flavor="sour") == {}
    assert source.merge_options(flavor="sweet") == {"flavor": "sweet"}
    assert source.merge_options(flavor="") == {}


def test_current_options_default():
    """current_options returns empty dict for default options."""
    source = FakeSource("default")
    assert source.current_options() == {}


@pytest.mark.parametrize(
    "option,value",
    (
        ("pressed", True),
        ("length", 1),
        ("unbounded", "all"),
        ("flavor", "curry"),
    ),
    ids=("bool", "int", "int_all", "text"),
)
def test_current_options_nondefault(option, value):
    """current_options returns the non-default options as a dict."""
    source = FakeSource("default", **{option: value})
    assert source.current_options() == {option: value}


@pytest.mark.parametrize(
    "option_type,option,bad_value",
    (
        ("bool", "pressed", 1),
        ("int", "length", "0"),
        ("int_all", "unbounded", "1"),
        ("text", "flavor", 1),
    ),
    ids=("bool", "int", "int_all", "text"),
)
def test_invalid_values(option_type, option, bad_value):
    """Invalid parameter values raise a ValueError."""
    with pytest.raises(ValueError) as err:
        FakeSource("fails", **{option: bad_value})
    assert option_type in str(err.value)


@pytest.mark.parametrize(
    "href,decoded",
    [
        (b"binary", "binary"),
        (b"%E7%A7%BB%E8%A1%8C%E4%BA%88%E5%AE%9A", "移行予定"),
        ("Slug#Anchor_\u2014_With_Dash", "Slug#Anchor_\u2014_With_Dash"),
    ],
)
def test_decode_href(href, decoded):
    """Source.decode_href() turns URL-encoded hrefs into unicode strings."""
    source = FakeSource("conversions")
    assert decoded == source.decode_href(href)


def test_source_error_str():
    """The Source.Error exception can be turned into a string."""
    error1 = Source.SourceError("A simple error")
    assert "%s" % error1 == "A simple error"
    error2 = Source.SourceError('A formatted error, like "%s" and %d.', "a string", 123)
    assert "%s" % error2 == 'A formatted error, like "a string" and 123.'


def test_gather_done_is_done():
    """A source that is done can still be gathered."""
    source = FakeSource("existing")
    source.state = source.STATE_DONE
    assert source.gather(mock_requester(), mock_storage()) == []
    assert source.state == source.STATE_DONE
    assert source.freshness == source.FRESH_UNKNOWN


def test_gather_load_storage_existing():
    """A source that is already in storage loads quickly."""
    source = FakeSource("existing")
    source.load_and_validate_existing = mock.Mock(return_value=(True, ["next"]))
    ret = source.gather(mock_requester(), mock_storage())
    assert ret == ["next"]
    assert source.state == source.STATE_DONE
    assert source.freshness == source.FRESH_NO


def test_gather_load_storage_error():
    """A source can raise an error when loading from storage."""
    source = FakeSource("existing")
    source.load_and_validate_existing = mock.Mock(
        side_effect=source.SourceError("Storage complained.")
    )
    ret = source.gather(mock_requester(), mock_storage())
    assert ret == []
    assert source.state == source.STATE_ERROR
    assert source.freshness == source.FRESH_UNKNOWN


def test_gather_load_prereqs_more_needed():
    """A source can request other sources as prerequisites."""
    source = FakeSource("needs_prereqs")
    data = {"needs": ["bonus"]}
    source.load_prereqs = mock.Mock(return_value=(False, data))
    ret = source.gather(mock_requester(), mock_storage())
    assert ret == ["bonus"]
    assert source.state == source.STATE_PREREQ
    assert source.freshness == source.FRESH_UNKNOWN


def test_gather_load_prereqs_error():
    """A source may raise an error when loading prerequisites."""
    source = FakeSource("bad_prereqs")
    source.load_prereqs = mock.Mock(side_effect=source.SourceError("bad"))
    ret = source.gather(mock_requester(), mock_storage())
    assert ret == []
    assert source.state == source.STATE_ERROR
    assert source.freshness == source.FRESH_UNKNOWN


def test_gather_save_data_error():
    """A source can fail when saving the data."""
    source = FakeSource("needs_prereqs")
    source.load_prereqs = mock.Mock(return_value=(True, {}))
    source.save_data = mock.Mock(side_effect=source.SourceError("failed"))
    ret = source.gather(mock_requester(), mock_storage())
    assert ret == []
    assert source.state == source.STATE_ERROR
    assert source.freshness == source.FRESH_YES


def test_gather_success_with_more_sources():
    """A source with all prereqs can request further sources."""
    source = FakeSource("needs_prereqs")
    source.load_prereqs = mock.Mock(return_value=(True, {}))
    source.save_data = mock.Mock(return_value=["bonus"])
    ret = source.gather(mock_requester(), mock_storage())
    assert ret == ["bonus"]
    assert source.state == source.STATE_DONE
    assert source.freshness == source.FRESH_YES
