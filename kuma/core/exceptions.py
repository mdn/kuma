class ProgrammingError(Exception):
    """Somebody made a mistake in the code."""


class DateTimeFormatError(Exception):
    """Called by the datetimeformat function when receiving invalid format."""

    pass


class FixtureMissingError(Exception):
    """Raise this if a fixture is missing"""
