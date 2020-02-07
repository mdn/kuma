"""Load test fixtures from a specification."""


import logging

from django.apps import apps
from django.contrib.auth.hashers import make_password

logger = logging.getLogger("kuma.scraper")


class FixtureLoader(object):
    """Load fixtures into the current database."""

    # Needed information about the supported Django models for fixtures
    # The key is the app_label.model_name, such as wiki.revision for Revision:
    #  Revision._meta.app_label == 'wiki'
    #  Revision._meta.model_name == 'revision'
    # The value is a dictionary of:
    # - natural_key: Properties used to find existing database records
    # - relations: Details of properties that are foreign keys
    # - filters: Methods to run on values before saving to the database
    model_metadata = {
        "account.emailaddress": {
            "natural_key": ("email",),
            "relations": {"user": {"link": "to_one", "resource": "users.user"}},
        },
        "auth.group": {
            "natural_key": ("name",),
            "relations": {
                "permissions": {"link": "to_many", "resource": "auth.permission"},
            },
        },
        "auth.permission": {
            "natural_key": ("codename",),
            "relations": {
                "content_type": {
                    "link": "to_one",
                    "resource": "contenttypes.contenttype",
                },
            },
        },
        "contenttypes.contenttype": {"natural_key": ("app_label", "model")},
        "database.constance": {"natural_key": ("key",)},
        "feeder.bundle": {
            "natural_key": ("shortname",),
            "relations": {"feeds": {"link": "to_many", "resource": "feeder.feed"}},
        },
        "feeder.feed": {"natural_key": ("shortname",)},
        "search.filter": {
            "natural_key": ("name", "slug"),
            "relations": {
                "group": {"link": "to_one", "resource": "search.filtergroup"},
                "tags": {"link": "to_many", "resource": "taggit.tag"},
            },
        },
        "search.filtergroup": {"natural_key": ("name", "slug")},
        "sites.site": {"natural_key": ("id",)},
        "socialaccount.socialaccount": {
            "natural_key": ("uid", "provider"),
            "relations": {"user": {"link": "to_one", "resource": "users.user"}},
        },
        "socialaccount.socialapp": {
            "natural_key": ("name",),
            "relations": {"sites": {"link": "to_many", "resource": "sites.site"}},
        },
        "taggit.tag": {"natural_key": ("name",)},
        "users.user": {
            "natural_key": ("username",),
            "relations": {"groups": {"link": "to_many", "resource": "auth.group"}},
            "filters": {"password": "make_password"},
        },
        "users.userban": {
            "natural_key": ("user", "by"),
            "relations": {
                "user": {"link": "to_one", "resource": "users.user"},
                "by": {"link": "to_one", "resource": "users.user"},
            },
        },
        "waffle.flag": {"natural_key": ("name",)},
        "waffle.switch": {"natural_key": ("name",)},
    }

    class NeedsDependency(Exception):
        """A fixture has an un-resolved dependency."""

        pass

    def __init__(self, specification):
        """Intialize with a specification dictionary."""
        self.instances = {}
        self.spec = self.parse_specification(specification)

    def parse_specification(self, specification):
        """Parse and validate the specification."""
        parsed = {}
        for model_id, items in specification.items():
            # Parse and validate the model
            metadata = self.model_metadata[model_id]
            natural_key_spec = metadata["natural_key"]
            relations = metadata.get("relations", {})
            filters = metadata.get("filters", {})
            assert apps.get_model(model_id)

            parsed.setdefault(model_id, [])
            for item_num, item in enumerate(items):
                # Parse and validate the natural key
                key = []
                for name in natural_key_spec:
                    relation = relations.get(name, {})
                    try:
                        value = item.pop(name)
                    except KeyError:
                        raise ValueError(
                            '%s %d: Needs key "%s"' % (model_id, item_num, name)
                        )
                    else:
                        if relation:
                            assert relation["link"] == "to_one"
                            key.append(tuple(value))
                        else:
                            key.append(value)

                data = {
                    "key": tuple(key),
                    "fields": {},
                    "relations": {},
                }

                # Parse and validate the remaining properties
                for name, value in item.items():
                    relation = relations.get(name, {})
                    if relation:
                        if relation["link"] == "to_one":
                            data["relations"][name] = tuple(value)
                        else:
                            assert relation["link"] == "to_many"
                            data["relations"][name] = [tuple(val) for val in value]
                    elif name in filters:
                        value_filter = getattr(self, filters[name])
                        data["fields"][name] = value_filter(value)
                    else:
                        data["fields"][name] = value

                parsed[model_id].append(data)
        return parsed

    def load(self):
        """Load items until complete or progress stops."""
        if not self.spec:
            return
        existing, loaded, pending = (0, 0, 0)
        cycle = 0
        while cycle == 0 or pending:
            cycle += 1
            last_counts = (existing, loaded, pending)
            existing, loaded, pending = self.load_cycle()
            logger.info(
                "Fixtures cycle %d: %d existing, %d loaded," " %d pending.",
                cycle,
                existing,
                loaded,
                pending,
            )
            if (existing, loaded, pending) == last_counts:
                raise RuntimeError("Dependency block detected.")

    def load_cycle(self):
        """
        Load as many items as we can this cycle.

        Returns a tuple of counts:
        * Existing items from previous cycles
        * Items loaded this cycle
        * Items that were unable to be loaded this cycle
        """
        existing, loaded, pending = 0, 0, 0
        for model_id, items in self.spec.items():
            metadata = self.model_metadata[model_id]
            Model = apps.get_model(model_id)

            self.instances.setdefault(model_id, {})
            for item in items:
                if item["key"] in self.instances[model_id]:
                    existing += 1
                else:
                    try:
                        instance = self.load_item(item, Model, metadata)
                    except self.NeedsDependency as nd:
                        relation, key = nd.args
                        logger.debug(
                            "%s %s requires %s %s",
                            model_id,
                            item["key"],
                            relation["resource"],
                            key,
                        )
                        pending += 1
                    else:
                        self.instances[model_id][item["key"]] = instance
                        loaded += 1
        return existing, loaded, pending

    def load_item(self, item, Model, metadata):
        """
        Attempt to create or update an item.

        Returns the instance if attempt suceeded.
        Raises NeedsDependency if a dependency must be created first.
        """
        natural_key_spec = metadata["natural_key"]
        relations = metadata.get("relations", {})

        # Check for required relations in the natural key
        for name, key in zip(natural_key_spec, item["key"]):
            relation = relations.get(name, {})
            if relation:
                instances = self.instances.get(relation["resource"], {})
                if key not in instances:
                    raise self.NeedsDependency(relation, key)

        # Check for required relations in other properties
        for name, value in item["relations"].items():
            relation = relations[name]
            if relation["link"] == "to_one":
                required = [value]
            else:
                required = value
            instances = self.instances.get(relation["resource"], {})
            for key in required:
                if key not in instances:
                    raise self.NeedsDependency(relation, key)

        # Prepare the items in the key
        key_dict = {}
        for name, key in zip(natural_key_spec, item["key"]):
            relation = relations.get(name, {})
            if relation:
                rel = self.instances[relation["resource"]][key]
                key_dict[name] = rel
            else:
                key_dict[name] = key

        # Prepare the other properties
        defaults = item["fields"].copy()
        for name, value in item["relations"].items():
            relation = relations[name]
            if relation["link"] == "to_one":
                rel = self.instances[relation["resource"]][value]
                defaults[name] = rel

        # Get or create the new instance. Set the non-relation properties
        # when creating an instance.
        instance, created = Model.objects.get_or_create(defaults=defaults, **key_dict)

        # For existing instances, set the properties
        if not created:
            for name, value in item["fields"].items():
                setattr(instance, name, value)
            for name, value in item["relations"].items():
                relation = relations[name]
                if relation["link"] == "to_one":
                    rel = self.instances[relation["resource"]][value]
                    setattr(instance, name, rel)
            instance.save()

        # Set the relations for new and existing instances
        for name, values in item["relations"].items():
            relation = relations[name]
            if relation["link"] == "to_many":
                for value in values:
                    rel = self.instances[relation["resource"]][value]
                    getattr(instance, name).add(rel)

        return instance

    def make_password(self, password):
        """Create a database hash for a password."""
        return make_password(password)
