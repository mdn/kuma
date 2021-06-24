class PrimaryRouter:

    app_labels = {"postgres": ["documenturls", "bookmarks"]}

    _app_labels_reversed = {}
    for db, labels in app_labels.items():
        for app_label in labels:
            _app_labels_reversed[app_label] = db

    def db_for_read(self, model, **hints):
        return self._app_labels_reversed.get(model._meta.app_label)

    def db_for_write(self, model, **hints):
        return self._app_labels_reversed.get(model._meta.app_label)

    def allow_relation(self, obj1, obj2, **hints):
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        # Check if it was one of the apps that was added since AFTER
        # Postgres was introduced to the stack.
        if app_label in self.app_labels.get(db, []):
            return True
        # It's important to *not* do `return False` here because that would
        # essentially mean "Do not run this migration with any database".
        # By doing a `return None` you let other database routers get a chance
        # to say yes to this migration.
        return None


class LegacyRouter:
    def db_for_read(self, model, **hints):
        return "default"

    def db_for_write(self, model, **hints):
        return "default"

    def allow_relation(self, obj1, obj2, **hints):
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return True
