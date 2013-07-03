# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from sumo.monkeypatch import URLWidget


class PatternURLWidget(URLWidget):
    """A URLWidget with a pattern attribute, set by self.pattern."""

    def render(self, *args, **kwargs):
        self.attrs['pattern'] = self.pattern
        return super(PatternURLWidget, self).render(*args, **kwargs)


class FacebookURLWidget(PatternURLWidget):
    """A URLWidget that requires a Facebook URL."""
    pattern = r'https?://(?:www\.)?facebook\.com/.+'


class TwitterURLWidget(PatternURLWidget):
    """A URLWidget that requires a Twitter URL."""
    pattern = r'https?://(?:www\.)?twitter\.com/.+'
