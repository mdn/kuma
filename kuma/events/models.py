import csv
import urllib2
from datetime import datetime

from django.db import models

from html5lib import sanitizer, HTMLParser


def parse_date(date_str):
    try:
        parsed_date = datetime.strptime(date_str, "%m/%d/%Y")
        parsed_date.strftime("%Y-%m-%d")
        return parsed_date
    except:
        return None


FIELD_MAP = {
    "date": ["Start Date", None, parse_date],
    "end_date": ["End Date", None, parse_date],
    "conference": ["Conference", None],
    "conference_link": ["Link", None],
    "location": ["Location", None],
    "people": ["Attendees", None],
    "description": ["Description", None],
    "done": ["Done", None],
    "materials": ["Materials URL", None],
}


def parse_header_line(header_line):
    for field_name in FIELD_MAP.keys():
        field = FIELD_MAP[field_name]
        if field[1] is None:
            try:
                FIELD_MAP[field_name][1] = header_line.index(field[0])
            except IndexError:
                FIELD_MAP[field_name][1] = ''
            except ValueError:
                FIELD_MAP[field_name][1] = ''


class Calendar(models.Model):
    """The Calendar spreadsheet"""

    shortname = models.CharField(max_length=255)
    url = models.URLField(
        help_text='URL of the google doc spreadsheet for events', unique=True)

    class Meta:
        db_table = 'devmo_calendar'

    def __unicode__(self):
        return self.shortname

    @classmethod
    def as_unicode(cls, events):
        parser = HTMLParser(tokenizer=sanitizer.HTMLSanitizer)
        for row in events:
            for idx, cell in enumerate(row):
                row[idx] = parser.parseFragment(unicode(cell, 'utf-8')).toxml()
            yield row

    @classmethod
    def parse_row(cls, doc_row):
        row = {}
        for field_name, field in FIELD_MAP.items():
            if len(doc_row) > field[1]:
                field_value = doc_row[field[1]]
            else:
                field_value = ''
            if len(field) >= 3 and callable(field[2]):
                field_value = field[2](field_value)
            row[field_name] = field_value
        return row

    def reload(self, data=None):
        events = []
        u = None

        if not data:
            try:
                u = urllib2.urlopen(self.url)
            except Exception:
                return False
        data = csv.reader(u) if u else data
        if not data:
            return False

        events = list(Calendar.as_unicode(data))
        Event.objects.filter(calendar=self).delete()

        # use column indices from header names so re-ordering
        # columns doesn't blow us up
        header_line = events.pop(0)
        parse_header_line(header_line)

        today = datetime.today()

        for event_line in events:
            event = None
            row = Calendar.parse_row(event_line)
            if row['date'] is None:
                continue
            if row['end_date'] is None:
                row['end_date'] = row['date']
            row['done'] = False
            if row['end_date'] < today:
                row['done'] = True
            row['end_date'] = row['end_date'].strftime("%Y-%m-%d")
            row['date'] = row['date'].strftime("%Y-%m-%d")
            for field_name in ('conference', 'location', 'people',
                               'description'):
                # Sometimes we still get here with non-ASCII data;
                # that will blow up on attempting to save, so we check
                # the text-based fields to make sure they decode
                # cleanly as ASCII, and force-decode them as UTF-8 if
                # they don't.
                try:
                    row[field_name].decode('ascii')
                except UnicodeDecodeError:
                    row[field_name] = row[field_name].decode('utf-8', 'ignore')

            try:
                event = Event(calendar=self, **row)
                event.save()
            except:
                continue


class Event(models.Model):
    """An event"""
    date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    conference = models.CharField(max_length=255)
    conference_link = models.URLField(blank=True)
    location = models.CharField(max_length=255)
    people = models.TextField()
    description = models.TextField()
    done = models.BooleanField(default=False)
    materials = models.URLField(blank=True)
    calendar = models.ForeignKey(Calendar)

    class Meta:
        ordering = ['date']
        db_table = 'devmo_event'

    def __unicode__(self):
        return '%s - %s, %s' % (self.date, self.conference, self.location)
