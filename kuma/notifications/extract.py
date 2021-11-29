import functools
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


def get_feature(bcd, feature):
    try:
        return functools.reduce(dict.get, feature.split("."), bcd) or {}
    except (TypeError, KeyError):
        return {}


class NotificationGenerator:
    text = "Notification for "

    def __init__(self, path, old_bcd, new_bcd):
        self.path = path
        self.old_bcd = old_bcd
        self.new_bcd = new_bcd
        self.old_feature = get_feature(old_bcd, path).get("__compat", None)
        self.new_feature = get_feature(new_bcd, path).get("__compat", None)

    def support(self):
        # Is this static?
        old_support = self.old_feature.get("support", {}) if self.old_feature else {}
        new_support = self.new_feature.get("support", {}) if self.new_feature else {}
        browsers = set(list(old_support.keys()) + list(new_support.keys()))

        for browser in browsers:
            yield browser, old_support.get(browser, {}), new_support.get(browser, {})

    def notification_text(self, template, browser):
        return template.format(feature=self.path, browser=browser)

    def compare(self, old, new):
        raise NotImplemented

    def generate_for_browsers(self):
        for browser, old, new in self.support():
            # ToDo: Review the spec and deal with lists
            if isinstance(old, list):
                old = old[0] if old else {}
            if isinstance(new, list):
                new = new[0] if new else {}

            if template := self.compare(old, new):
                yield self.notification_text(template, browser)

    def generate(self):
        notifications = list(self.generate_for_browsers())
        if len(notifications) > 3:
            return [self.text + "multiple browsers"]
        elif len(notifications) > 0:
            return [self.text + ", ".join(notifications)]
        return [self.text + i for i in notifications]


class NowSupported(NotificationGenerator):
    text = "Now supported in "

    def compare(self, old, new):
        if new.get("version_added") and not old.get("version_added"):
            return f"{{browser}} {new['version_added']}"


class Removed(NotificationGenerator):
    text = "No longer supported in "

    def compare(self, old, new):
        if (old.get("version_added") and not old.get("version_removed")) and (
            not new.get("version_added") or new.get("version_removed")
        ):
            return "{browser}"


class SubFeatures(NotificationGenerator):
    text = "We have new data about subfeatures for "

    def compare(self, old, new):
        if new != old:
            return f"{{browser}} {new.get('version_added', '')}"

    def generate_for_browsers(self):
        for child in walk(self.new_bcd, self.path):
            self.path = child[0]
            yield from super().generate_for_browsers()


generators = [NowSupported, Removed, SubFeatures]
