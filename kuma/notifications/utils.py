import json

from kuma.notifications.models import Watch, Notification, NotificationData


# browsers: dict = json.loads(open("browsers.json").read())


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
    return browser;
    # return browsers.get(browser, {info: browser}).get(info, "")


def process_changes(changes, dry_run=False):
    for change in changes:
        browser = get_browser_info(change.get("browser", ""))
        browser_preview = get_browser_info(change.get("browser", ""), "preview_name")

        if change["event"] == "added_stable":
            for feature in change["features"]:
                publish_notification(
                    feature["path"],
                    f"is now stable in {browser} {change['version']}",
                    dry_run=dry_run,
                    data=change,
                )
        elif change["event"] == "remove_stable":
            for feature in change["features"]:
                publish_notification(
                    feature["path"],
                    f"is no longer supported in {browser} {change['version']}",
                    dry_run=dry_run,
                    data=change,
                )
        elif change["event"] == "added_preview":
            for feature in change["features"]:
                publish_notification(
                    feature["path"],
                    f"is now in development in {browser} {browser_preview}",
                    dry_run=dry_run,
                    data=change,
                )
        elif change["event"] == "added_nonnull":
            browser_list = [
                get_browser_info(i["browser"]) for i in change["support_changes"]
            ]
            if len(browser_list) == 1:
                text = browser_list[0]
            else:
                text = ",".join(browser_list[:-1]) + f", and {browser_list[-1]}"
            publish_notification(
                change["path"],
                f"has more complete compatibility data for {text}",
                dry_run=dry_run,
                data=change,
            )
        elif change["event"] == "added_subfeatures":
            n = len(change["subfeatures"])
            publish_notification(
                change["path"],
                f"is now reporting compatibility data for {n} subfeature{'s'[:n^1]}",
                dry_run=dry_run,
                data=change,
            )
