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
        return functools.reduce(dict.get, feature.split("."), bcd)
    except (TypeError, KeyError):
        return None


class NotificationGenerator:
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

    def generate(self):
        for browser, old, new in self.support():
            # ToDo: This is not covered in the spec.
            if isinstance(old, list):
                old = old[0] if old else {}
            if isinstance(new, list):
                new = new[0] if new else {}

            if template := self.compare(old, new):
                yield self.notification_text(template, browser)


class NowSupported(NotificationGenerator):
    def compare(self, old, new):
        if new.get("version_added") and not old.get("version_added"):
            return f"{{browser}} {new['version_added']}"

    def generate(self):
        notifications = list(super().generate())
        if len(notifications) > 3:
            return ["Now supported in multiple browsers"]
        elif len(notifications) > 0:
            return ["Now supported in " + ", ".join(notifications)]
        return notifications


class Removed(NotificationGenerator):
    def compare(self, old, new):
        if (old.get("version_added") and not old.get("version_removed")) and (
            not new.get("version_added") or new.get("version_removed")
        ):
            return "{browser}"

    def generate(self):
        notifications = list(super().generate())
        if len(notifications) > 3:
            return ["No longer supported in multiple browsers"]
        elif len(notifications) > 0:
            return ["No longer supported in " + ", ".join(notifications)]
        return notifications


class SubFeatures(NotificationGenerator):
    def compare(self, old, new):
        if new != old:
            return f"We have new data about subfeatures for {{browser}} {new['version_added']}"

    def generate(self):
        for child in walk(self.new_bcd, self.path):
            self.path = child[0]
            yield from super().generate()


generators = [NowSupported, Removed, SubFeatures]
