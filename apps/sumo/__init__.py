# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# Just importing monkeypatch does the trick - don't remove this line
from sumo import monkeypatch


class ProgrammingError(Exception):
    """Somebody made a mistake in the code."""
