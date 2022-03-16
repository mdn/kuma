from collections import defaultdict

from kuma.notifications.browsers import browsers
from kuma.notifications.models import Notification, NotificationData, Watch


def publish_notification(path, text, dry_run=False, data=None):
    # This traverses down the path to see if there's top level watchers
    parts = path.split(".")
    suffix = []
    while len(parts) > 0:
        subpath = ".".join(parts)
        watcher = Watch.objects.filter(path=subpath).first()
        suffix.append(parts.pop())

        if not watcher:
            continue

        # Add the suffix based on the path to the title.
        # Since suffix contains the current title (which should be an exact match)
        # we use the suffix as title (after reversing the order).
        title = reversed(suffix)
        title = ".".join(title)
        if not dry_run:
            notification_data, _ = NotificationData.objects.get_or_create(
                title=title,
                text=text,
                data=data,
                type="compat",
                page_url=watcher.url,
            )
            for user in watcher.users.all():
                Notification.objects.create(notification=notification_data, user=user)


def get_browser_info(browser, preview=False):
    name = browsers.get(browser, {"name": browser}).get("name", "")

    if preview:
        return browsers.get(browser, {"preview_name": browser, "name": browser}).get(
            "preview_name", name
        )

    return name


def pluralize(browser_list):
    if len(browser_list) == 1:
        return browser_list[0]
    else:
        return ", ".join(browser_list[:-1]) + f", and {browser_list[-1]}"


BROWSER_GROUP = {
    "firefox": "firefox",
    "firefox_android": "firefox",
    "chrome": "chrome",
    "chrome_android": "chrome",
    "edge": "chrome",
    "webview_android": "chrome",
    "deno": "deno",
    "safari": "safari",
    "safari_ios": "safari",
    "ie": "ie",
    "nodejs": "nodejs",
    "opera": "opera",
    "opera_android": "opera",
    "samsunginternet_android": "samsunginternet_android",
}

COPY = {
    "added_stable": "Supported in ",
    "removed_stable": "Removed from ",
    "added_preview": "In development in ",
}


def process_changes(changes, dry_run=False):
    notifications = []
    for change in changes:
        if change["event"] in ["added_stable", "removed_stable", "added_preview"]:
            groups = defaultdict(list)
            for browser_data in change["browsers"]:
                browser = get_browser_info(
                    browser_data["browser"],
                    change["event"] == "added_preview",
                )
                groups[BROWSER_GROUP.get(browser_data["browser"], browser)].append(
                    {
                        "browser": f"{browser} {browser_data['version']}",
                        "data": change,
                    }
                )
            for group in groups.values():
                browser_list = pluralize([i["browser"] for i in group])
                notifications.append(
                    {
                        "path": change["path"],
                        "text": COPY[change["event"]] + browser_list,
                        "data": [i["data"] for i in group],
                    }
                )

        elif change["event"] == "added_subfeatures":
            n = len(change["subfeatures"])
            notifications.append(
                {
                    "path": change["path"],
                    "text": f"{n} compatibility subfeature{'s'[:n ^ 1]} added",
                    "data": change,
                }
            )
        elif change["event"] == "added_nonnull":
            browser_list = [
                get_browser_info(i["browser"]) for i in change["support_changes"]
            ]
            text = pluralize(browser_list)
            notifications.append(
                {
                    "path": change["path"],
                    "text": f"More complete compatibility data added for {text}",
                    "data": change,
                }
            )

    for notification in notifications:
        publish_notification(**notification, dry_run=dry_run)
