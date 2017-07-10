# -*- coding: utf-8 -*-
"""py.test fixtures for kuma.wiki.tests."""
import json
import base64
from datetime import datetime
from collections import namedtuple

import pytest

from ..models import Document, DocumentZone, Revision


BannedUser = namedtuple('BannedUser', 'user ban')
Contributors = namedtuple('Contributors', 'valid banned inactive')
DocWithContributors = namedtuple('DocWithContributors', 'doc contributors')
DocHierarchy = namedtuple('DocHierarchy', 'top middle_top middle_bottom bottom')
KumaScriptToolbox = namedtuple(
    'KumaScriptToolbox',
    'errors errors_as_headers macros_response'
)


@pytest.fixture
def wiki_user(db, django_user_model):
    """A test user."""
    return django_user_model.objects.create(
        username='wiki_user',
        email='wiki_user@example.com',
        date_joined=datetime(2017, 4, 14, 12, 0))


@pytest.fixture
def wiki_user_2(db, django_user_model):
    """A second test user."""
    return django_user_model.objects.create(
        username='wiki_user_2',
        email='wiki_user_2@example.com',
        date_joined=datetime(2017, 4, 17, 10, 30))


@pytest.fixture
def wiki_user_3(db, django_user_model):
    """A third test user."""
    return django_user_model.objects.create(
        username='wiki_user_3',
        email='wiki_user_3@example.com',
        date_joined=datetime(2017, 4, 23, 11, 45))


@pytest.fixture
def inactive_wiki_user(db, django_user_model):
    """An inactive test user."""
    return django_user_model.objects.create(
        is_active=False,
        username='wiki_user_slacker',
        email='wiki_user_slacker@example.com',
        date_joined=datetime(2017, 4, 19, 10, 58))


@pytest.fixture
def banned_wiki_user(db, django_user_model, wiki_user):
    """A banned test user."""
    user = django_user_model.objects.create(
        username='bad_wiki_user',
        email='bad_wiki_user@example.com',
        date_joined=datetime(2017, 4, 18, 9, 15)
    )
    ban = user.bans.create(by=wiki_user, reason='because')
    return BannedUser(user=user, ban=ban)


@pytest.fixture
def root_doc(wiki_user):
    """A newly-created top-level English document."""
    root_doc = Document.objects.create(
        locale='en-US', slug='Root', title='Root Document')
    Revision.objects.create(
        document=root_doc,
        creator=wiki_user,
        content='<p>Getting started...</p>',
        title='Root Document',
        created=datetime(2017, 4, 14, 12, 15))
    return root_doc


@pytest.fixture
def create_revision(root_doc):
    """A revision that created an English document."""
    return root_doc.revisions.first()


@pytest.fixture
def edit_revision(root_doc, wiki_user):
    """A revision that edits an English document."""
    root_doc.current_revision = Revision.objects.create(
        document=root_doc,
        creator=wiki_user,
        content='<p>The root document.</p>',
        comment='Done with initial version.',
        created=datetime(2017, 4, 14, 12, 30))
    root_doc.save()
    return root_doc.current_revision


@pytest.fixture
def trans_doc(create_revision, wiki_user):
    """Translate the root document into French."""
    trans_doc = Document.objects.create(
        locale='fr',
        parent=create_revision.document,
        slug='Racine',
        title='Racine du Document')
    Revision.objects.create(
        document=trans_doc,
        creator=wiki_user,
        based_on=create_revision,
        content='<p>Mise en route...</p>',
        title='Racine du Document',
        created=datetime(2017, 4, 14, 12, 20))
    return trans_doc


@pytest.fixture
def trans_revision(trans_doc):
    return trans_doc.current_revision


@pytest.fixture
def trans_edit_revision(trans_doc, edit_revision, wiki_user):
    """A further edit to the translated document."""
    trans_doc.current_revision = Revision.objects.create(
        document=trans_doc,
        creator=wiki_user,
        based_on=edit_revision,
        content='<p>Le document racine.</p>',
        title='Racine du Document',
        created=datetime(2017, 4, 14, 20, 25))
    trans_doc.save()
    return trans_doc.current_revision


@pytest.fixture
def doc_hierarchy_with_zones(settings, wiki_user, wiki_user_2, wiki_user_3):
    top_doc = Document.objects.create(
        locale='en-US',
        slug='top',
        title='Top Document'
    )
    Revision.objects.create(
        document=top_doc,
        creator=wiki_user,
        content='<p>Top...</p>',
        title='Top Document',
        created=datetime(2017, 4, 24, 13, 49)
    )
    top_de_doc = Document.objects.create(
        locale='de',
        slug='oben',
        title='Oben Dokument',
        rendered_html='<p>Oben...</p>',
        parent=top_doc
    )
    Revision.objects.create(
        document=top_de_doc,
        creator=wiki_user_2,
        based_on=top_doc.current_revision,
        content='<p>Oben...</p>',
        title='Oben Dokument',
        created=datetime(2017, 4, 30, 10, 3)
    )
    top_fr_doc = Document.objects.create(
        locale='fr',
        slug='haut',
        title='Haut Document',
        rendered_html='<p>Haut...</p>',
        parent=top_doc
    )
    Revision.objects.create(
        document=top_fr_doc,
        creator=wiki_user_3,
        based_on=top_doc.current_revision,
        content='<p>Haut...</p>',
        title='Haut Document',
        is_approved=True,
        created=datetime(2017, 4, 30, 12, 1)
    )
    top_it_doc = Document.objects.create(
        locale='it',
        slug='superiore',
        title='Superiore Documento',
        rendered_html='<p>Superiore...</p>',
        parent=top_doc
    )
    Revision.objects.create(
        document=top_it_doc,
        creator=wiki_user_2,
        based_on=top_doc.current_revision,
        content='<p>Superiore...</p>',
        title='Superiore Documento',
        created=datetime(2017, 4, 30, 11, 17)
    )
    middle_top_doc = Document.objects.create(
        locale='en-US',
        slug='top/middle-top',
        title='Middle-Top Document',
        parent_topic=top_doc
    )
    Revision.objects.create(
        document=middle_top_doc,
        creator=wiki_user,
        content='<p>Middle-Top...</p>',
        title='Middle-Top Document',
        created=datetime(2017, 4, 24, 13, 50)
    )
    middle_bottom_doc = Document.objects.create(
        locale='en-US',
        slug='top/middle-top/middle-bottom',
        title='Middle-Bottom Document',
        parent_topic=middle_top_doc
    )
    Revision.objects.create(
        document=middle_bottom_doc,
        creator=wiki_user,
        content='<p>Middle-Bottom...</p>',
        title='Middle-Bottom Document',
        created=datetime(2017, 4, 24, 13, 51)
    )
    bottom_doc = Document.objects.create(
        locale='en-US',
        slug='top/middle-top/middle-bottom/bottom',
        title='Bottom Document',
        parent_topic=middle_bottom_doc
    )
    Revision.objects.create(
        document=bottom_doc,
        creator=wiki_user,
        content='<p>Bottom...</p>',
        title='Bottom Document',
        created=datetime(2017, 4, 24, 13, 52)
    )
    DocumentZone.objects.create(
        document=top_doc,
        css_slug='lindsey',
        url_root='fleetwood-mac'
    )
    DocumentZone.objects.create(
        document=middle_top_doc,
        css_slug='bobby',
        url_root='spinners'
    )
    DocumentZone.objects.create(
        document=top_de_doc,
        css_slug='berlin',
        url_root='berlin'
    )
    DocumentZone.objects.create(
        document=top_it_doc,
        url_root='florence'
    )
    settings.PIPELINE_CSS.update({
        'zone-lindsey': {
            'source_filenames': (
                'styles/zone-lindsey.scss',
            ),
            'output_filename': 'build/styles/zone-lindsey.css',
        },
        'zone-bobby': {
            'source_filenames': (
                'styles/zone-bobby.scss',
            ),
            'output_filename': 'build/styles/zone-bobby.css',
        },
        'zone-berlin': {
            'source_filenames': (
                'styles/zone-berlin.scss',
            ),
            'output_filename': 'build/styles/zone-berlin.css',
        },
        'zones': {
            'source_filenames': (
                'styles/zones.scss',
            ),
            'output_filename': 'build/styles/zones.css',
        }
    })
    return DocHierarchy(
        top=top_doc,
        middle_top=middle_top_doc,
        middle_bottom=middle_bottom_doc,
        bottom=bottom_doc,
    )


@pytest.fixture
def root_doc_with_mixed_contributors(root_doc, wiki_user, wiki_user_2,
                                     inactive_wiki_user, banned_wiki_user):
    """
    A top-level English document with mixed contributors (some are valid,
    some are banned, and some are inactive).
    """
    root_doc.current_revision = Revision.objects.create(
        document=root_doc,
        creator=wiki_user_2,
        content='<p>The root document.</p>',
        comment='Done with the initial version.',
        created=datetime(2017, 4, 17, 12, 35))
    root_doc.save()

    root_doc.current_revision = Revision.objects.create(
        document=root_doc,
        creator=inactive_wiki_user,
        content='<p>The root document re-envisioned.</p>',
        comment='Done with the second revision.',
        created=datetime(2017, 4, 18, 10, 15))
    root_doc.save()

    root_doc.current_revision = Revision.objects.create(
        document=root_doc,
        creator=banned_wiki_user.user,
        content='<p>The root document re-envisioned with malice.</p>',
        comment='Nuke the previous revision.',
        created=datetime(2017, 4, 19, 10, 15))
    root_doc.save()

    return DocWithContributors(
        doc=root_doc,
        contributors=Contributors(
            valid=[wiki_user_2, wiki_user],
            banned=banned_wiki_user,
            inactive=inactive_wiki_user
        )
    )


@pytest.fixture
def ks_toolbox():
    errors = {
        "logs": [
            {"level": "debug",
             "message": "Message #1",
             "args": ['TestError', {},
                      {'name': 'SomeMacro',
                       'token': {'args': 'arguments here'}}],
             "time": "12:32:03 GMT-0400 (EDT)",
             "timestamp": "1331829123101000"},
            {"level": "warning",
             "message": "Error: unable to load: SomeMacro2",
             "args": ['TestError', {}, {'name': 'SomeMacro2'}],
             "time": "12:33:58 GMT-0400 (EDT)",
             "timestamp": "1331829238052000"},
            {"level": "error",
             "message": "Syntax error at line 88...",
             "args": [
                 'DocumentParsingError',
                 'Syntax error at line 88...',
                 {'error': {'line': 88, 'column': 65}}
             ],
             "time": "12:33:59 GMT-0400 (EDT)",
             "timestamp": "1331829238053000"},
            {"level": "info",
             "message": "Message #3",
             "args": ['TestError'],
             "time": "12:34:22 GMT-0400 (EDT)",
             "timestamp": "1331829262403000"},
            {"level": "debug",
             "message": "Message #4",
             "time": "12:32:03 GMT-0400 (EDT)",
             "timestamp": "1331829123101000"},
            {"level": "warning",
             "message": "Message #5",
             "time": "12:33:58 GMT-0400 (EDT)",
             "timestamp": "1331829238052000"},
            {"level": "info",
             "message": "Message #6",
             "time": "12:34:22 GMT-0400 (EDT)",
             "timestamp": "1331829262403000"},
        ]
    }

    d_json = json.dumps(errors)
    d_b64 = base64.encodestring(d_json)
    d_lines = [x for x in d_b64.split("\n") if x]

    # Headers are case-insensitive, so let's drive that point home.
    p = ['firelogger', 'FIRELOGGER', 'FireLogger']
    fl_uid = 8675309
    errors_as_headers = {}
    for i in range(0, len(d_lines)):
        errors_as_headers['%s-%s-%s' % (p[i % len(p)], fl_uid, i)] = d_lines[i]

    macros_response = {
        'json': {
            'loader': 'FileLoader',
            'can_list_macros': True,
            'macros': [
                {
                    'name': 'SomeMacro',
                    'filename': 'SomeMacro.ejs'
                },
                {
                    'name': 'SomeMacro2',
                    'filename': 'SomeMacro2.ejs'
                }
            ]
        },
        'headers': {
            'Content-Type': 'application/json; charset=utf-8'
        }
    }

    return KumaScriptToolbox(errors, errors_as_headers, macros_response)
