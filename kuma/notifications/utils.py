import json
from collections import defaultdict

from kuma.notifications.models import Watch, Notification, NotificationData
from kuma.notifications.browsers import browsers


def publish_notification(path, text, dry_run=False, data=None):
    watcher = Watch.objects.filter(path=path).first()
    if not watcher:
        print(path, text)
        return

    print(watcher.title, text)
    if not dry_run:
        notification_data, _ = NotificationData.objects.get_or_create(
            title=watcher.title,
            text=text,
            data=data,
            type="compat",
            page_url=watcher.url,
        )
        for user in watcher.users.all():
            Notification.objects.create(notification=notification_data, user=user)


def get_browser_info(browser, info="name"):
    return browsers.get(browser, {info: browser}).get(info, "")


def pluralize(browser_list):
    if len(browser_list) == 1:
        return browser_list[0]
    else:
        return ", ".join(browser_list[:-1]) + f", and {browser_list[-1]}"


def process_changes(changes, dry_run=False):
    copy = {
        "added_stable": "is supported in ",
        "removed_stable": "is no longer supported in ",
        "added_preview": "is in development in ",
    }
    mergable = {key: defaultdict(list) for key in copy.keys()}
    notifications = []
    for change in changes:
        browser = get_browser_info(change.get("browser", ""))
        browser_preview = get_browser_info(change.get("browser", ""), "preview_name")

        if change["event"] == "added_stable":
            for browser_data in change["browsers"]:
                browser = get_browser_info(browser_data["browser"])
                mergable["added_stable"][change["path"]].append(
                    {
                        "browser": f"{browser} {browser_data['version']}",
                        "data": change,
                    }
                )

        elif change["event"] == "removed_stable":
            for browser_data in change["browsers"]:
                browser = get_browser_info(browser_data["browser"])
                mergable["removed_stable"][change["path"]].append(
                    {
                        "browser": f"{browser} {browser_data['version']}",
                        "data": change,
                    }
                )
        elif change["event"] == "added_preview":
            for browser_data in change["browsers"]:
                browser = get_browser_info(browser_data["browser"])
                browser_preview = get_browser_info(
                    browser_data["browser"], "preview_name"
                )
                mergable["added_preview"][change["path"]].append(
                    {
                        "browser": f"{browser} {browser_preview}",
                        "data": change,
                    }
                )
        elif change["event"] == "added_subfeatures":
            n = len(change["subfeatures"])
            notifications.append(
                {
                    "path": change["path"],
                    "text": f"is now reporting compatibility data for {n} subfeature{'s'[:n ^ 1]}",
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
                    "text": f"has more complete compatibility data for {text}",
                    "data": change,
                }
            )

    for key, group in mergable.items():
        for path, content in group.items():
            if not content:
                continue
            browser_list = pluralize([i["browser"] for i in content])
            notifications.append(
                {
                    "path": path,
                    "text": copy[key] + browser_list,
                    "data": [i["data"] for i in content],
                }
            )

    for notification in notifications:
        publish_notification(**notification, dry_run=dry_run)
