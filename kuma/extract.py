import itertools
import json
import sys
from collections.abc import Mapping

bcd = json.loads(open("bcd.json").read())


def walk(data, path=None, depth=sys.maxsize):
    if depth == 0:
        return

    if not path:
        path = ""

    for key in data:
        if not isinstance(data[key], Mapping):
            continue

        if key == "__compat":
            # This is an element with compat information
            yield path, data[key]
        else:
            yield from walk(
                data[key], path=f"{path}{'.' if path else ''}{key}", depth=depth - 1
            )


# Added in IE, removed in Opera (Android)
DATABASE = {
    "css.properties.font-variant.css_fonts_shorthand": {
        "description": "CSS Fonts Module Level 3 shorthand",
        "support": {
            "chrome": {"version_added": "52"},
            "chrome_android": {"version_added": "52"},
            "edge": {"version_added": "79"},
            "firefox": {"version_added": "34"},
            "firefox_android": {"version_added": "34"},
            "ie": {"version_added": "4"},
            "opera": {"version_added": "39"},
            "opera_android": {"version_added": False},
            "safari": {"version_added": "9.1"},
            "safari_ios": {"version_added": "9.3"},
            "samsunginternet_android": {"version_added": "6.0"},
            "webview_android": {"version_added": "52"},
        },
        "status": {"experimental": False, "standard_track": True, "deprecated": False},
    },
    "html.elements.area.ping": {
        "support": {
            "chrome": {"version_added": "12"},
            "chrome_android": {"version_added": "18"},
            "edge": {"version_added": "17"},
            "firefox": {
                "version_added": True,
                "flags": [
                    {
                        "type": "preference",
                        "name": "browser.send_pings",
                        "value_to_set": "true",
                    }
                ],
            },
            "firefox_android": {
                "version_added": True,
                "version_removed": "79",
                "flags": [
                    {
                        "type": "preference",
                        "name": "browser.send_pings",
                        "value_to_set": "true",
                    }
                ],
            },
            "ie": {"version_added": "8"},
            "opera": {"version_added": "15"},
            "opera_android": {"version_added": "14"},
            "safari": {"version_added": "6"},
            "safari_ios": {"version_added": "6"},
            "samsunginternet_android": {"version_added": "1.0"},
            "webview_android": {"version_added": False},
        },
        "status": {"experimental": False, "standard_track": True, "deprecated": False},
    },
}

# Assumption Qs
#  * Is the list of browsers static? can we make it a global variable? (yes, but get it from the data)
#  * Translations? (prob no)
#  * What's the best way to generate the name for a feature? (From the content repo)
#  * Do we have a very old version of the compat data? (generate it from repo)


class NotificationGenerator:
    def __init__(self, old_data, new_data):
        old_name, old_support = old_data
        new_name, new_support = new_data
        if old_name != new_name:
            raise ValueError("InvalidData: Not the same feature")

        self.path = new_name
        self.old = old_support
        self.new = new_support

    def support(self):
        # Is this static?
        old_support = self.old.get("support", {})
        new_support = self.new.get("support", {})
        browsers = set(list(old_support.keys()) + list(new_support.keys()))

        for browser in browsers:
            yield browser, old_support.get(browser, {}), new_support.get(browser, {})

    def notification_text(self, template, browser):
        return template.format(feature=self.path, browser=browser)

    def compare(self, old, new):
        raise NotImplemented

    def generate(self):
        for browser, old, new in self.support():
            if template := self.compare(old, new):
                yield self.notification_text(template, browser)


class NowSupported(NotificationGenerator):
    def compare(self, old, new):
        if new.get("version_added") and not old.get("version_added"):
            return "{feature} is now supported in {browser}"


class Removed(NotificationGenerator):
    def compare(self, old, new):
        if (old.get("version_added") and not old.get("version_removed")) and (
            not new.get("version_added") or new.get("version_removed")
        ):
            return "{feature} is no longer supported in {browser}"


generators = [NowSupported, Removed]


def generate_notifications():
    # itertools.islice(walk(bcd), 50)
    for feature in walk(bcd):
        for generator in generators:
            if new_feature := DATABASE.get(feature[0]):
                yield from generator(feature, (feature[0], new_feature)).generate()
