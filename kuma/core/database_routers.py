class PrimaryRouter:

    app_labels = {"postgres": set(["documenturls", "bookmarks"])}

    legacy_app_labels = set(["wiki", "search", "authtoken", "authkeys", "taggit"])
    legacy_model_names = set(["userban", "ipban"])

    app_labels_reversed = {}
    for db, labels in app_labels.items():
        for app_label in labels:
            app_labels_reversed[app_label] = db

    def db_for_read(self, model, **hints):
        return self.app_labels_reversed.get(model._meta.app_label)

    def db_for_write(self, model, **hints):
        return self.app_labels_reversed.get(model._meta.app_label)

    def allow_relation(self, obj1, obj2, **hints):
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        # Check if it was one of the apps that was added since AFTER
        # Postgres was introduced to the stack.
        if app_label in self.app_labels.get(db, []):
            return True

        # Django can't operate if the database doesn't have a django_content_type
        # table.
        # if db == "postgres" and app_label in ("contenttypes", "sites"):
        #     return True

        # Because of how Django migrations work with a multi-db, all apps and models
        # will be created even if you don't read or write from them. But some
        # apps and models we will never want to allow in the primary database.
        if app_label in self.legacy_app_labels or model_name in self.legacy_model_names:
            return False

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
        if PrimaryRouter.app_labels_reversed.get(app_label):
            return False
        return True
