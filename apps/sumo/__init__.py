# Just importing monkeypatch does the trick - don't remove this line
from sumo import monkeypatch


class ProgrammingError(Exception):
    """Somebody made a mistake in the code."""
