"""Scrape a user profile from a Kuma website."""


from django.core.management.base import CommandError

from . import ScrapeCommand


class Command(ScrapeCommand):
    help = "Scrape a wiki document."

    def add_arguments(self, parser):
        """Add arguments for scraping an MDN wiki document."""
        parser.add_argument("--email", help="Set the email address")
        parser.add_argument(
            "--social", help="Include social links", action="store_true"
        )
        parser.add_argument(
            "--force", help="Update existing User record", action="store_true"
        )
        parser.add_argument(
            "url", metavar="url_or_profile", help="URL or profile name of a MDN user"
        )

    def parse_url_or_profile(self, url_or_profile):
        host, ssl, path = self.parse_url_or_path(url_or_profile)
        if path.startswith("/en-US"):
            profile = path.split("/")[-1]
        else:
            profile = path
        return host, ssl, profile

    def handle(self, *arg, **options):
        self.setup_logging(options["verbosity"])
        url_or_profile = options["url"]
        host, ssl, profile = self.parse_url_or_profile(url_or_profile)
        scraper = self.make_scraper(host=host, ssl=ssl)

        params = {}
        for param in ("social", "force"):
            if options[param]:
                params[param] = options[param]
        if options["email"]:
            params["email"] = options["email"].decode("utf8")
        scraper.add_source("user", profile, **params)

        scraper.scrape()
        source = scraper.sources["user:" + profile]
        if source.state == source.STATE_ERROR:
            raise CommandError('Unable to scrape user "%s".' % profile)
        elif source.freshness == source.FRESH_NO and not options["force"]:
            self.stderr.write(
                'User "%s" already exists. Use --force to update.' % profile
            )
