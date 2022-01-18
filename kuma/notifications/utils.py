from kuma.notifications.models import Watch, Notification, NotificationData


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


def process_changes(changes, dry_run=False):
    for change in changes:
        if change["event"] == "added_stable":
            for feature in change["features"]:
                publish_notification(
                    feature["path"],
                    f"is now stable in {change['browser']} {change['version']}",
                    dry_run=dry_run,
                    data=change,
                )
        elif change["event"] == "remove_stable":
            for feature in change["features"]:
                publish_notification(
                    feature["path"],
                    f"is no longer supported in {change['browser']} {change['version']}",
                    dry_run=dry_run,
                    data=change,
                )
        elif change["event"] == "added_preview":
            for feature in change["features"]:
                publish_notification(
                    feature["path"],
                    f"{feature['path']} is now in preview in {change['browser']}",
                    dry_run=dry_run,
                    data=change,
                )
        elif change["event"] == "added_nonnull":
            browsers = [i["browser"] for i in change["support_changes"]]
            if len(browsers) == 1:
                text = browsers[0]
            elif len(browsers) > 3:
                text = f"{len(browsers)} browsers"
            else:
                text = ",".join(browsers[:-1]) + f", and {browsers[-1]}"
            publish_notification(
                change["path"],
                f"Support information added for {text}",
                dry_run=dry_run,
                data=change,
            )
        elif change["event"] == "added_subfeatures":
            publish_notification(
                change["path"], "has new subfeatures", dry_run=dry_run, data=change
            )
