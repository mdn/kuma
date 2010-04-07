"""
Tests for the search (sphinx) app.
"""
import os
import shutil
import time

from django.test import client
from django.db import connection

from nose import SkipTest
import test_utils
import json

from manage import settings
from sumo.urlresolvers import reverse
from search.utils import start_sphinx, stop_sphinx, reindex
from search.clients import WikiClient


def create_extra_tables():
    """
    Creates extra tables necessary for Sphinx indexing.

    XXX: This is the Wrong Way&trade; to do this! I'm only falling back
    to this option because I've exhausted all the other possibilities.
    This should GO AWAY when we get rid of the tiki_objects mess.
    """
    cursor = connection.cursor()

    cursor.execute('SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0;')

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS `tiki_freetags` (
          `tagId` int(10) unsigned NOT NULL AUTO_INCREMENT,
          `tag` varchar(30) NOT NULL DEFAULT '',
          `raw_tag` varchar(50) NOT NULL DEFAULT '',
          `lang` varchar(16) DEFAULT NULL,
          PRIMARY KEY (`tagId`)
        ) ENGINE=MyISAM AUTO_INCREMENT=12176 DEFAULT CHARSET=latin1;
        """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS `tiki_freetagged_objects` (
          `tagId` int(12) NOT NULL AUTO_INCREMENT,
          `objectId` int(11) NOT NULL DEFAULT '0',
          `user` varchar(200) NOT NULL DEFAULT '',
          `created` int(14) NOT NULL DEFAULT '0',
          PRIMARY KEY (`tagId`,`user`,`objectId`),
          KEY `tagId` (`tagId`),
          KEY `user` (`user`),
          KEY `objectId` (`objectId`)
        ) ENGINE=MyISAM AUTO_INCREMENT=12176 DEFAULT CHARSET=latin1;
        """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS `tiki_objects` (
          `objectId` int(12) NOT NULL AUTO_INCREMENT,
          `type` varchar(50) DEFAULT NULL,
          `itemId` varchar(255) DEFAULT NULL,
          `description` text,
          `created` int(14) DEFAULT NULL,
          `name` varchar(200) DEFAULT NULL,
          `href` varchar(200) DEFAULT NULL,
          `hits` int(8) DEFAULT NULL,
          PRIMARY KEY (`objectId`),
          KEY `type` (`type`,`itemId`),
          KEY `itemId` (`itemId`,`type`)
        ) ENGINE=MyISAM AUTO_INCREMENT=35581 DEFAULT CHARSET=latin1;
        """)

    cursor.execute("""
        INSERT IGNORE INTO tiki_objects (objectId, type, itemId, name) VALUES
            (79, 'wiki page', 'Firefox Support Home Page',
                'Firefox Support Home Page'),
            (84, 'wiki page', 'Style Guide', 'Style Guide'),
            (62, 'wiki page', 'Video or audio does not play',
                'Video or audio does not play');
        """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS `tiki_category_objects` (
          `catObjectId` int(12) NOT NULL DEFAULT '0',
          `categId` int(12) NOT NULL DEFAULT '0',
          PRIMARY KEY (`catObjectId`,`categId`),
          KEY `categId` (`categId`)
        ) ENGINE=MyISAM DEFAULT CHARSET=latin1;
        """)

    cursor.execute("""
        INSERT IGNORE INTO tiki_category_objects (catObjectId, categId) VALUES
            (79, 8), (84, 23), (62, 1), (62, 13),
            (62, 14), (62, 19), (62, 25);
        """)

    cursor.execute('SET SQL_NOTES=@OLD_SQL_NOTES;')


def destroy_extra_tables():
    """
    Removes the extra tables created by create_extra_tables.
    """

    cursor = connection.cursor()

    cursor.execute('SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0;')
    cursor.execute('DROP TABLE IF EXISTS tiki_category_objects')
    cursor.execute('DROP TABLE IF EXISTS tiki_objects')
    cursor.execute('DROP TABLE IF EXISTS tiki_freetagged_objects')
    cursor.execute('DROP TABLE IF EXISTS tiki_freetags')
    cursor.execute('SET SQL_NOTES=@OLD_SQL_NOTES;')


class SphinxTestCase(test_utils.TransactionTestCase):
    """
    This test case type can setUp and tearDown the sphinx daemon.  Use this
    when testing any feature that requires sphinx.
    """

    fixtures = ['forums.json', 'threads.json', 'pages.json', 'categories.json']
    sphinx = True
    sphinx_is_running = False

    def setUp(self):

        create_extra_tables()

        if not SphinxTestCase.sphinx_is_running:
            if not settings.SPHINX_SEARCHD or not settings.SPHINX_INDEXER:
                raise SkipTest()

            os.environ['DJANGO_ENVIRONMENT'] = 'test'

            if os.path.exists('/tmp/k'):
                shutil.rmtree('/tmp/k')

            os.makedirs('/tmp/k/data')
            os.makedirs('/tmp/k/log')
            os.makedirs('/tmp/k/etc')
            reindex()
            start_sphinx()
            time.sleep(1)
            SphinxTestCase.sphinx_is_running = True

    @classmethod
    def tearDownClass(cls):

        destroy_extra_tables()

        if SphinxTestCase.sphinx_is_running:
            stop_sphinx()
            SphinxTestCase.sphinx_is_running = False


class SearchTest(SphinxTestCase):

    def test_indexer(self):
        wc = WikiClient()
        results = wc.query('practice')
        self.assertNotEquals(0, len(results))

    def test_category_filter(self):
        wc = WikiClient()
        results = wc.query('', ({'filter': 'category', 'value': [13]},))
        self.assertNotEquals(0, len(results))

    def test_category_exclude(self):
        c = client.Client()
        response = c.get(reverse('search'),
                         {'q': 'audio', 'format': 'json', 'w': 3})
        self.assertNotEquals(0, json.loads(response.content)['total'])

        response = c.get(reverse('search'),
                         {'q': 'audio', 'category': -13,
                          'format': 'json', 'w': 1})
        self.assertEquals(0, json.loads(response.content)['total'])
