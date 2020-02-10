"""Shared interface for data sources."""


import re
from urllib.parse import unquote


class Source(object):
    """
    An MDN data source.

    This represents data that requires a request to a running MDN server.

    Derived classes should set some class variables to customize behaviour:
    PARAM_NAME - The attribute name of the "key" parameter for the data source
    OPTIONS - A dictionary of option names to (type, default value) pairs.
    """

    # Scraping states
    STATES = (
        "Initializing",
        "Gathering Requirements",
        "Done",
        "Error",
    )
    STATE_INIT, STATE_PREREQ, STATE_DONE, STATE_ERROR = STATES

    # Freshness of scraped data
    FRESHNESS = (
        "Unknown",
        "Fresh",
        "Existing",
    )
    FRESH_UNKNOWN, FRESH_YES, FRESH_NO = FRESHNESS

    # Friendly name of the source's key parameter
    PARAM_NAME = "param"

    # Types of source options. Used when merging options, to determine if
    # the new or existing option value should win, possible resetting scraping.
    OPTION_TYPES = {
        "bool",  # True > False
        "int",  # 2 > 1 > 0
        "int_all",  # 'all' > 2 > 0
        "text",  # any new value > old value > ''
    }

    # The scrape options for this source, defaulting to no valid settings
    # Format is name -> (option_type, default value)
    OPTIONS = {}

    class SourceError(Exception):
        """An error raised during gathering."""

        def __init__(self, *args, **kwargs):
            self.format = args[0]
            self.format_args = args[1:]
            super(Source.SourceError, self).__init__(*args, **kwargs)

        def __str__(self):
            return self.format % self.format_args

    def __init__(self, param, **options):
        """Initialize an MDN data source."""
        setattr(self, self.PARAM_NAME, param)
        self.state = self.STATE_INIT
        self.freshness = self.FRESH_UNKNOWN

        for name, params in self.OPTIONS.items():
            option_type, default = params
            assert option_type in self.OPTION_TYPES
            self.assert_option_value_allowed(option_type, default)
            setattr(self, name, default)

        self.merge_options(**options)

    def assert_option_value_allowed(self, option_type, value):
        """Assert that an option value is valid."""
        if option_type == "bool":
            valid = value is True or value is False
        elif option_type == "int":
            valid = value == int(value)
        elif option_type == "int_all":
            valid = value == "all" or value == int(value)
        else:
            assert option_type == "text"
            valid = isinstance(value, str)

        if not valid:
            raise ValueError(
                'invalid value "%s" for type "%s"' % (repr(value), option_type)
            )

    def merge_options(self, **options):
        """
        Merge new options with current options, returning changed options.

        The new option wins if it is "higher" than the existing option.
        """
        changed = {}
        for name, value in options.items():
            option_type = self.OPTIONS[name][0]
            self.assert_option_value_allowed(option_type, value)
            current = getattr(self, name)
            if option_type == "bool":
                if value and not current:
                    changed[name] = value
                    setattr(self, name, True)
            elif option_type == "int":
                value = int(value)
                if value > current:
                    changed[name] = value
                    setattr(self, name, value)
            elif option_type == "int_all":
                if str(value).lower() == "all":
                    if current != "all":
                        changed[name] = "all"
                        setattr(self, name, "all")
                else:
                    value = int(value)
                    if value > current:
                        changed[name] = value
                        setattr(self, name, value)
            else:
                assert option_type == "text"
                if value and value != current:
                    changed[name] = value
                    setattr(self, name, value)
        if changed:
            self.state = self.STATE_INIT
        return changed

    def current_options(self):
        """Return the current non-default options."""
        current = {}
        for name, spec in self.OPTIONS.items():
            opt_type, default = spec
            value = getattr(self, name, default)
            if value != default:
                current[name] = value
        return current

    def decode_href(self, href):
        """Convert URL-escaped href attributes to unicode."""
        if isinstance(href, bytes):
            uhref = href.decode("ascii")
        else:
            uhref = href
        decoded = unquote(uhref)
        assert isinstance(decoded, str)
        return decoded

    def gather(self, requester, storage):
        """
        Gather prerequisites and store data for a source.

        Return is a list of source specifications, such as prerequisites
        needed to load the source, or follow-on sources identified by the
        source.
        """
        if self.state == self.STATE_INIT:
            # If possible, load and validate existing data for the source
            try:
                load_return = self.load_and_validate_existing(storage)
            except self.SourceError as error:
                self.error = error
                self.state = self.STATE_ERROR
            else:
                has_existing, next_sources = load_return
                if has_existing:
                    self.state = self.STATE_DONE
                    self.freshness = self.FRESH_NO
                    return next_sources
                else:
                    self.state = self.STATE_PREREQ

        if self.state == self.STATE_PREREQ:
            try:
                has_prereqs, data = self.load_prereqs(requester, storage)
            except self.SourceError as error:
                self.error = error
                self.state = self.STATE_ERROR
            else:
                if has_prereqs:
                    self.freshness = self.FRESH_YES
                    # Save the data and load follow-on sources
                    try:
                        next_sources = self.save_data(storage, data)
                    except self.SourceError as error:
                        self.error = error
                        self.state = self.STATE_ERROR
                    else:
                        self.state = self.STATE_DONE
                        return next_sources
                else:
                    # Return the additional prerequisite sources
                    return data["needs"]

        # Load no more sources in a "done" state
        assert self.state in [self.STATE_ERROR, self.STATE_DONE]
        return []

    def load_and_validate_existing(self, storage):
        """Default: Can not load existing data from storage."""
        return False, []


class DocumentBaseSource(Source):
    """Shared functionality for MDN Document sources."""

    PARAM_NAME = "path"

    re_path = re.compile(r"/(?P<locale>[^/]+)/docs/(?P<slug>.*)")

    # Standard options for Document-based sources
    STANDARD_DOC_OPTIONS = {
        "force": ("bool", False),  # Update existing Document records
        "depth": ("int_all", 0),  # Scrape the topic tree to this depth
        "revisions": ("int", 1),  # Scrape this many past revisions
        "translations": ("bool", False),  # Scrape the alternate translations
    }

    def __init__(self, path, **options):
        super(DocumentBaseSource, self).__init__(path, **options)
        if path != unquote(path):
            raise ValueError(f"URL-encoded path {path!r}")
        try:
            self.locale, self.slug = self.locale_and_slug(path)
        except ValueError:
            self.locale, self.slug = None, None

    def locale_and_slug(self, path):
        """Extract a document locale and slug from a path."""
        match = self.re_path.match(path)
        if match:
            return match.groups()
        else:
            raise ValueError(f"Not a valid document path {path!r}")

    @property
    def parent_slug(self):
        if self.slug and "/" in self.slug:
            return "/".join(self.slug.split("/")[:-1])

    @property
    def parent_path(self):
        if self.parent_slug:
            return f"/{self.locale}/docs/{self.parent_slug}"
