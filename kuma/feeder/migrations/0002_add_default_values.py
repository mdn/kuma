# -*- coding: utf-8 -*-
from south.db import db
from south.v2 import DataMigration


class Migration(DataMigration):

    def forwards(self, orm):
        db.execute("INSERT INTO `feeder_bundle` VALUES (3,'twitter-addons'),(2,'twitter-mobile'),(4,'twitter-mozilla'),(1,'twitter-web'),(6,'updates-addons'),(7,'updates-mobile'),(5,'updates-mozilla'),(8,'updates-web');")
        db.execute("INSERT INTO `feeder_bundle_feeds` VALUES (25,1,2),(24,1,3),(26,1,5),(22,2,4),(21,3,7),(23,4,8),(29,5,13),(27,6,10),(28,7,6),(30,8,1);")
        db.execute("INSERT INTO `feeder_feed` VALUES (1,'moz-hacks','','http://hacks.mozilla.org/feed/','','2011-03-24 10:00:28',1,'',50,'2011-03-24 10:00:28','2011-03-24 10:00:28'),(2,'tw-mozhacks','','http://twitter.com/statuses/user_timeline/45496942.rss','','2011-03-24 10:00:28',1,'',50,'2011-03-24 10:00:28','2011-03-24 10:00:28'),(3,'tw-mozillaweb','','http://twitter.com/statuses/user_timeline/38209403.rss','','2011-03-24 10:00:28',1,'',50,'2011-03-24 10:00:28','2011-03-24 10:00:28'),(4,'tw-mozmobile','','http://twitter.com/statuses/user_timeline/67033966.rss','','2011-03-24 10:00:28',1,'',50,'2011-03-24 10:00:28','2011-03-24 10:00:28'),(5,'tw-mozillaqa','','http://twitter.com/statuses/user_timeline/24752152.rss','','2011-03-24 10:00:28',1,'',50,'2011-03-24 10:00:28','2011-03-24 10:00:28'),(6,'planet-mobile','','http://planet.firefox.com/mobile/rss20.xml','','2011-03-24 10:00:28',1,'',50,'2011-03-24 10:00:28','2011-03-24 10:00:28'),(7,'tw-mozamo','','http://twitter.com/statuses/user_timeline/15383463.rss','','2011-03-24 10:00:28',1,'',50,'2011-03-24 10:00:28','2011-03-24 10:00:28'),(8,'tw-planetmozilla','','http://twitter.com/statuses/user_timeline/39292665.rss','','2011-03-24 10:00:28',1,'',50,'2011-03-24 10:00:28','2011-03-24 10:00:28'),(9,'moz-hacks-comments','','http://hacks.mozilla.org/comments/feed/','','2011-03-24 10:00:28',1,'',50,'2011-03-24 10:00:28','2011-03-24 10:00:28'),(10,'amo-blog','','http://blog.mozilla.com/addons/feed/','','2011-03-24 10:00:28',1,'',50,'2011-03-24 10:00:28','2011-03-24 10:00:28'),(11,'amo-blog-comments','','http://blog.mozilla.com/addons/comments/feed/','','2011-03-24 10:00:28',1,'',50,'2011-03-24 10:00:28','2011-03-24 10:00:28'),(12,'amo-forums','','https://forums.addons.mozilla.org/feed.php','','2011-03-24 10:00:28',1,'',50,'2011-03-24 10:00:28','2011-03-24 10:00:28'),(13,'about-mozilla','','http://blog.mozilla.com/about_mozilla/feed/atom/','','2011-03-24 10:00:28',1,'',50,'2011-03-24 10:00:28','2011-03-24 10:00:28'),(14,'mdc-latest','','https://developer.mozilla.org/@api/deki/site/feed','','2011-03-24 10:00:28',1,'',50,'2011-03-24 10:00:28','2011-03-24 10:00:28');")

    def backwards(self, orm):
        "Write your backwards methods here."
        db.clear_table('feeder_bundle')
        db.clear_table('feeder_bundle_feeds')
        db.clear_table('feeder_feed')

    models = {
        'feeder.bundle': {
            'Meta': {'object_name': 'Bundle'},
            'feeds': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'bundles'", 'blank': 'True', 'to': "orm['feeder.Feed']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'shortname': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'})
        },
        'feeder.entry': {
            'Meta': {'ordering': "['-last_published']", 'unique_together': "(('feed', 'guid'),)", 'object_name': 'Entry'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'feed': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'entries'", 'to': "orm['feeder.Feed']"}),
            'guid': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_published': ('django.db.models.fields.DateTimeField', [], {}),
            'raw': ('django.db.models.fields.TextField', [], {}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'visible': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        'feeder.feed': {
            'Meta': {'object_name': 'Feed'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'disabled_reason': ('django.db.models.fields.CharField', [], {'max_length': '2048', 'blank': 'True'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'etag': ('django.db.models.fields.CharField', [], {'max_length': '140'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'keep': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {}),
            'shortname': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '140'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '2048'})
        }
    }

    complete_apps = ['feeder']
    symmetrical = True
