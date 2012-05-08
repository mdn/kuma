USE kuma;

-- Brute force cleaning to make way for South migrations
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS `devmo_event` CASCADE;
DROP TABLE IF EXISTS `devmo_calendar` CASCADE;
DROP TABLE IF EXISTS `wiki_document` CASCADE;
DROP TABLE IF EXISTS `wiki_documenttag` CASCADE;
DROP TABLE IF EXISTS `wiki_revision` CASCADE;
DROP TABLE IF EXISTS `wiki_firefoxversion` CASCADE; 
DROP TABLE IF EXISTS `wiki_operatingsystem` CASCADE;
DROP TABLE IF EXISTS `wiki_helpfulvote` CASCADE;
DROP TABLE IF EXISTS `wiki_relateddocument` CASCADE;
DROP TABLE IF EXISTS `wiki_editortoolbar` CASCADE;
DROP TABLE IF EXISTS `wiki_reviewtaggedrevision` CASCADE;
DROP TABLE IF EXISTS `wiki_reviewtag` CASCADE;
DROP TABLE IF EXISTS `wiki_taggeddocument` CASCADE;

-- Change site to developer-dev
UPDATE django_site set domain = 'developer-dev.mozilla.org', name = 'developer-dev.mozilla.org';

ALTER TABLE actioncounters_actioncounterunique ENGINE=InnoDB;
ALTER TABLE actioncounters_testmodel ENGINE=InnoDB;
ALTER TABLE auth_group ENGINE=InnoDB;
ALTER TABLE auth_group_permissions ENGINE=InnoDB;
ALTER TABLE auth_message ENGINE=InnoDB;
ALTER TABLE auth_permission ENGINE=InnoDB;
ALTER TABLE auth_user ENGINE=InnoDB;
ALTER TABLE auth_user_groups ENGINE=InnoDB;
ALTER TABLE auth_user_user_permissions ENGINE=InnoDB;
ALTER TABLE constance_config ENGINE=InnoDB;
ALTER TABLE contentflagging_contentflag ENGINE=InnoDB;
ALTER TABLE demos_submission ENGINE=InnoDB;
ALTER TABLE django_admin_log ENGINE=InnoDB;
ALTER TABLE django_content_type ENGINE=InnoDB;
ALTER TABLE django_session ENGINE=InnoDB;
ALTER TABLE django_site ENGINE=InnoDB;
ALTER TABLE feeder_bundle ENGINE=InnoDB;
ALTER TABLE feeder_bundle_feeds ENGINE=InnoDB;
ALTER TABLE feeder_entry ENGINE=InnoDB;
ALTER TABLE feeder_feed ENGINE=InnoDB;
ALTER TABLE gallery_image ENGINE=InnoDB;
ALTER TABLE gallery_video ENGINE=InnoDB;
ALTER TABLE notifications_eventwatch ENGINE=InnoDB;
ALTER TABLE notifications_watch ENGINE=InnoDB;
ALTER TABLE notifications_watchfilter ENGINE=InnoDB;
ALTER TABLE schema_version ENGINE=InnoDB;
ALTER TABLE south_migrationhistory ENGINE=InnoDB;
ALTER TABLE tagging_tag ENGINE=InnoDB;
ALTER TABLE tagging_taggeditem ENGINE=InnoDB;
ALTER TABLE taggit_tag ENGINE=InnoDB;
ALTER TABLE taggit_taggeditem ENGINE=InnoDB;
ALTER TABLE threadedcomments_freethreadedcomment ENGINE=InnoDB;
ALTER TABLE threadedcomments_testmodel ENGINE=InnoDB;
ALTER TABLE threadedcomments_threadedcomment ENGINE=InnoDB;
ALTER TABLE user_profiles ENGINE=InnoDB;
ALTER TABLE users_emailchange ENGINE=InnoDB;
ALTER TABLE users_profile ENGINE=InnoDB;
ALTER TABLE users_registrationprofile ENGINE=InnoDB;
ALTER TABLE waffle_flag ENGINE=InnoDB;
ALTER TABLE waffle_flag_groups ENGINE=InnoDB;
ALTER TABLE waffle_flag_users ENGINE=InnoDB;
ALTER TABLE waffle_sample ENGINE=InnoDB;
ALTER TABLE waffle_switch ENGINE=InnoDB;

USE wikidb;

DROP TABLE IF EXISTS `config`;
CREATE TABLE `config` (
  `config_id` int(10) unsigned NOT NULL auto_increment,
  `config_key` varchar(255) NOT NULL,
  `config_value` text NOT NULL,
  PRIMARY KEY  (`config_id`),
  KEY `config_key` (`config_key`)
) ENGINE=MyISAM AUTO_INCREMENT=76 DEFAULT CHARSET=utf8;

--
-- Dumping data for table `config`
--

LOCK TABLES `config` WRITE;
/*!40000 ALTER TABLE `config` DISABLE KEYS */;
INSERT INTO `config` VALUES (30,'@id','default'),(31,'admin',''),(32,'admin/email','lorchard@mozilla.com'),(33,'cache',''),(34,'cache/master','request'),(35,'db-catalog','wikidb'),(36,'db-options','pooling=true; Connection Timeout=5; Connection Lifetime=30; Protocol=socket; Min Pool Size=2; Max Pool Size=50; Connection Reset=false;character set=utf8;ProcedureCacheSize=25;Use Procedure Bodies=true;'),(37,'db-port','3306'),(38,'db-server','localhost'),(39,'db-user','wikiuser'),(40,'editor',''),(41,'editor/safe-html','true'),(42,'files',''),(43,'files/blacklisted-disposition-mimetypes',''),(44,'files/blocked-extensions','html, htm, exe, vbs, scr, reg, bat, com, htm, html, xhtml'),(45,'files/force-text-extensions','htm, html, xhtml, bat, reg, sh'),(46,'files/imagemagick-extensions','bmp, jpg, jpeg, png, gif'),(47,'files/imagemagick-max-size','2000000'),(48,'files/max-file-size','268435456'),(49,'files/whitelisted-disposition-mimetypes','text/plain, text/xml, application/xml, application/pdf, application/msword, application/vnd.ms-excel, application/vnd.ms-powerpoint, application/vnd.openxmlformats-officedocument.wordprocessingml.document, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.openxmlformats-officedocument.presentationml.presentation, application/vnd.oasis.opendocument.presentation, application/vnd.oasis.opendocument.spreadsheet, application/vnd.oasis.opendocument.text, application/x-shockwave-flash'),(50,'host','*'),(51,'languages','en,ar,ca,cs,de,el,es,fa,fi,fr,he,hr,hu,it,ja,ka,ko,nl,pl,pt,ro,ru,th,tr,uk,vi,zh-cn,zh-tw'),(52,'license',''),(53,'security',''),(54,'security/admin-user-for-impersonation','Admin'),(55,'security/allow-anon-account-creation','true'),(56,'security/api-key','GFxaNVK37fLPsFEYM7NwdIuNpGIiFTOX'),(57,'security/cookie-expire-secs','604800'),(58,'security/new-account-role','Contributor'),(59,'storage',''),(60,'storage/fs',''),(61,'storage/fs/path','/var/www/dekiwiki/attachments'),(62,'storage/s3',''),(63,'storage/s3/bucket',''),(64,'storage/s3/prefix',''),(65,'storage/s3/privatekey',''),(66,'storage/s3/publickey',''),(67,'storage/s3/timeout',''),(68,'storage/type','fs'),(69,'ui',''),(70,'ui/analytics-key','UA-68075-16'),(71,'ui/banned-words',''),(72,'ui/language','en-us'),(73,'ui/sitename','MDN'),(74,'ui/skin','Transitional'),(75,'ui/template','mdn');
/*!40000 ALTER TABLE `config` ENABLE KEYS */;
UNLOCK TABLES;

DROP TABLE IF EXISTS `service_config`;
CREATE TABLE `service_config` (
  `config_id` int(10) unsigned NOT NULL auto_increment,
  `service_id` int(4) unsigned NOT NULL,
  `config_name` char(255) NOT NULL,
  `config_value` text,
  PRIMARY KEY  (`config_id`)
) ENGINE=MyISAM AUTO_INCREMENT=64 DEFAULT CHARSET=utf8;

--
-- Dumping data for table `service_config`
--

LOCK TABLES `service_config` WRITE;
/*!40000 ALTER TABLE `service_config` DISABLE KEYS */;
INSERT INTO `service_config` VALUES (34,2,'manifest','http://scripts.mindtouch.com/accuweather.xml'),(2,3,'manifest','http://scripts.mindtouch.com/addthis.xml'),(37,5,'manifest','http://scripts.mindtouch.com/dhtml.xml'),(36,6,'manifest','http://scripts.mindtouch.com/digg.xml'),(39,8,'manifest','http://scripts.mindtouch.com/flickr.xml'),(41,9,'manifest','http://scripts.mindtouch.com/flowplayer.xml'),(43,12,'manifest','http://scripts.mindtouch.com/gravatar.xml'),(44,15,'manifest','http://scripts.mindtouch.com/linkedin.xml'),(48,20,'manifest','http://scripts.mindtouch.com/pagebus.xml'),(10,21,'manifest','http://scripts.mindtouch.com/paypal.xml'),(46,22,'manifest','http://scripts.mindtouch.com/scratch.xml'),(12,23,'manifest','http://scripts.mindtouch.com/scribd.xml'),(50,25,'manifest','http://scripts.mindtouch.com/skype.xml'),(55,26,'manifest','http://scripts.mindtouch.com/spoiler.xml'),(54,29,'manifest','http://scripts.mindtouch.com/syntax.xml'),(56,31,'manifest','http://scripts.mindtouch.com/twitter.xml'),(57,32,'manifest','http://scripts.mindtouch.com/widgetbox.xml'),(59,36,'manifest','http://scripts.mindtouch.com/editgrid.xml'),(58,35,'manifest','http://scripts.mindtouch.com/yuimediaplayer.xml'),(60,37,'manifest','http://scripts.mindtouch.com/lightbox.xml'),(61,38,'manifest','http://scripts.mindtouch.com/quicktime.xml'),(63,39,'manifest','http://scripts.mindtouch.com/rtm.xml'),(62,40,'manifest','http://scripts.mindtouch.com/zoho.xml');
/*!40000 ALTER TABLE `service_config` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `service_prefs`
--

DROP TABLE IF EXISTS `service_prefs`;
CREATE TABLE `service_prefs` (
  `pref_id` int(10) unsigned NOT NULL auto_increment,
  `service_id` int(4) unsigned NOT NULL,
  `pref_name` char(255) NOT NULL,
  `pref_value` text,
  PRIMARY KEY  (`pref_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `service_prefs`
--

LOCK TABLES `service_prefs` WRITE;
/*!40000 ALTER TABLE `service_prefs` DISABLE KEYS */;
/*!40000 ALTER TABLE `service_prefs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `services`
--

DROP TABLE IF EXISTS `services`;
CREATE TABLE `services` (
  `service_id` int(4) unsigned NOT NULL auto_increment,
  `service_type` varchar(255) NOT NULL,
  `service_sid` varchar(255) default NULL,
  `service_uri` varchar(255) default NULL,
  `service_description` mediumtext,
  `service_local` tinyint(1) unsigned NOT NULL default '1',
  `service_enabled` tinyint(1) unsigned NOT NULL default '1',
  `service_last_status` text,
  `service_last_edit` timestamp NOT NULL default CURRENT_TIMESTAMP on update CURRENT_TIMESTAMP,
  PRIMARY KEY  (`service_id`)
) ENGINE=MyISAM AUTO_INCREMENT=45 DEFAULT CHARSET=utf8;

--
-- Dumping data for table `services`
--

LOCK TABLES `services` WRITE;
/*!40000 ALTER TABLE `services` DISABLE KEYS */;
INSERT INTO `services` VALUES (1,'AUTH','http://services.mindtouch.com/deki/draft/2006/11/dekiwiki','local://4b8285ae06f9bb86a355b4d00ab31f92/deki','Local',1,1,'','2011-07-11 19:55:59'),(2,'EXT','sid://mindtouch.com/2007/12/dekiscript',NULL,'AccuWeather',1,1,'System.Exception: unable to initialize service (async operation timed out)\n  at MindTouch.Dream.DreamService+<CreateService_Helper>d__19.MoveNext () [0x00000] in <filename unknown>:0 \n  at MindTouch.Tasking.Coroutine.Continue () [0x00000] in <filename unknown>:0 \n   --- End of exception stack trace ---\n   at MindTouch.Dream.DreamService.CreateService_Helper(String path, String sid, XDoc config, Result`1 result)\n   --- End of coroutine stack trace ---','2011-07-11 19:55:59'),(3,'ext','sid://mindtouch.com/2007/12/dekiscript',NULL,'AddThis',1,0,NULL,'2011-07-11 19:55:59'),(4,'EXT','sid://mindtouch.com/2007/12/dapper','local://4b8285ae06f9bb86a355b4d00ab31f92/deki/services/default/4','Dapper',1,1,'','2011-07-11 19:55:59'),(6,'EXT','sid://mindtouch.com/2007/12/dekiscript',NULL,'Digg',1,1,'System.Exception: unable to initialize service (async operation timed out)\n  at MindTouch.Dream.DreamService+<CreateService_Helper>d__19.MoveNext () [0x00000] in <filename unknown>:0 \n  at MindTouch.Tasking.Coroutine.Continue () [0x00000] in <filename unknown>:0 \n   --- End of exception stack trace ---\n   at MindTouch.Dream.DreamService.CreateService_Helper(String path, String sid, XDoc config, Result`1 result)\n   --- End of coroutine stack trace ---','2011-07-11 19:55:59'),(8,'EXT','sid://mindtouch.com/2007/12/dekiscript',NULL,'Flickr',1,1,'System.Exception: unable to initialize service (async operation timed out)\n  at MindTouch.Dream.DreamService+<CreateService_Helper>d__19.MoveNext () [0x00000] in <filename unknown>:0 \n  at MindTouch.Tasking.Coroutine.Continue () [0x00000] in <filename unknown>:0 \n   --- End of exception stack trace ---\n   at MindTouch.Dream.DreamService.CreateService_Helper(String path, String sid, XDoc config, Result`1 result)\n   --- End of coroutine stack trace ---','2011-07-11 19:55:59'),(9,'EXT','sid://mindtouch.com/2007/12/dekiscript',NULL,'FlowPlayer',1,1,'System.Exception: unable to initialize service (async operation timed out)\n  at MindTouch.Dream.DreamService+<CreateService_Helper>d__19.MoveNext () [0x00000] in <filename unknown>:0 \n  at MindTouch.Tasking.Coroutine.Continue () [0x00000] in <filename unknown>:0 \n   --- End of exception stack trace ---\n   at MindTouch.Dream.DreamService.CreateService_Helper(String path, String sid, XDoc config, Result`1 result)\n   --- End of coroutine stack trace ---','2011-07-11 19:55:59'),(10,'ext','sid://mindtouch.com/2007/06/google',NULL,'Google',1,0,NULL,'2011-07-11 19:55:59'),(11,'ext','sid://mindtouch.com/2007/06/graphviz',NULL,'Graphviz',1,0,NULL,'2011-07-11 19:55:59'),(12,'EXT','sid://mindtouch.com/2007/12/dekiscript',NULL,'Gravatar',1,1,'System.Exception: unable to initialize service (async operation timed out)\n  at MindTouch.Dream.DreamService+<CreateService_Helper>d__19.MoveNext () [0x00000] in <filename unknown>:0 \n  at MindTouch.Tasking.Coroutine.Continue () [0x00000] in <filename unknown>:0 \n   --- End of exception stack trace ---\n   at MindTouch.Dream.DreamService.CreateService_Helper(String path, String sid, XDoc config, Result`1 result)\n   --- End of coroutine stack trace ---','2011-07-11 19:55:59'),(13,'ext','sid://mindtouch.com/2007/06/imagemagick',NULL,'ImageMagick',1,0,NULL,'2011-07-11 19:55:59'),(14,'ext','sid://mindtouch.com/2008/02/jira',NULL,'Jira',1,0,NULL,'2011-07-11 19:55:59'),(15,'EXT','sid://mindtouch.com/2007/12/dekiscript',NULL,'LinkedIn',1,1,'System.Exception: unable to initialize service (async operation timed out)\n  at MindTouch.Dream.DreamService+<CreateService_Helper>d__19.MoveNext () [0x00000] in <filename unknown>:0 \n  at MindTouch.Tasking.Coroutine.Continue () [0x00000] in <filename unknown>:0 \n   --- End of exception stack trace ---\n   at MindTouch.Dream.DreamService.CreateService_Helper(String path, String sid, XDoc config, Result`1 result)\n   --- End of coroutine stack trace ---','2011-07-11 19:55:59'),(16,'ext','sid://mindtouch.com/2008/01/mantis',NULL,'Mantis',1,0,NULL,'2011-07-11 19:55:59'),(17,'ext','sid://mindtouch.com/2007/06/math',NULL,'Math',1,0,NULL,'2011-07-11 19:55:59'),(18,'EXT','sid://mindtouch.com/2007/06/media','local://4b8285ae06f9bb86a355b4d00ab31f92/deki/services/default/18','Multimedia',1,1,'','2011-07-11 19:55:59'),(19,'ext','sid://mindtouch.com/2007/06/mysql',NULL,'MySql',1,0,NULL,'2011-07-11 19:55:59'),(7,'EXT','sid://mindtouch.com/2007/06/feed','local://4b8285ae06f9bb86a355b4d00ab31f92/deki/services/default/7','Atom/RSS Feeds',1,1,'','2011-07-11 19:55:59'),(21,'ext','sid://mindtouch.com/2007/12/dekiscript',NULL,'PayPal',1,0,NULL,'2011-07-11 19:55:59'),(22,'EXT','sid://mindtouch.com/2007/12/dekiscript',NULL,'Scratch',1,1,'System.Exception: unable to initialize service (async operation timed out)\n  at MindTouch.Dream.DreamService+<CreateService_Helper>d__19.MoveNext () [0x00000] in <filename unknown>:0 \n  at MindTouch.Tasking.Coroutine.Continue () [0x00000] in <filename unknown>:0 \n   --- End of exception stack trace ---\n   at MindTouch.Dream.DreamService.CreateService_Helper(String path, String sid, XDoc config, Result`1 result)\n   --- End of coroutine stack trace ---','2011-07-11 19:55:59'),(23,'ext','sid://mindtouch.com/2007/12/dekiscript',NULL,'Scribd',1,0,NULL,'2011-07-11 19:55:59'),(24,'EXT','sid://mindtouch.com/2008/02/silverlight','local://4b8285ae06f9bb86a355b4d00ab31f92/deki/services/default/24','Silverlight',1,1,'','2011-07-11 19:55:59'),(25,'EXT','sid://mindtouch.com/2007/12/dekiscript',NULL,'Skype',1,1,'System.Exception: unable to initialize service (async operation timed out)\n  at MindTouch.Dream.DreamService+<CreateService_Helper>d__19.MoveNext () [0x00000] in <filename unknown>:0 \n  at MindTouch.Tasking.Coroutine.Continue () [0x00000] in <filename unknown>:0 \n   --- End of exception stack trace ---\n   at MindTouch.Dream.DreamService.CreateService_Helper(String path, String sid, XDoc config, Result`1 result)\n   --- End of coroutine stack trace ---','2011-07-11 19:55:59'),(26,'EXT','sid://mindtouch.com/2007/12/dekiscript',NULL,'Spoiler',1,1,'System.Exception: unable to initialize service (async operation timed out)\n  at MindTouch.Dream.DreamService+<CreateService_Helper>d__19.MoveNext () [0x00000] in <filename unknown>:0 \n  at MindTouch.Tasking.Coroutine.Continue () [0x00000] in <filename unknown>:0 \n   --- End of exception stack trace ---\n   at MindTouch.Dream.DreamService.CreateService_Helper(String path, String sid, XDoc config, Result`1 result)\n   --- End of coroutine stack trace ---','2011-07-11 19:55:59'),(27,'ext','sid://mindtouch.com/2008/02/svn',NULL,'Subversion',1,0,NULL,'2011-07-11 19:55:59'),(28,'EXT','sid://mindtouch.com/2008/05/svg','local://4b8285ae06f9bb86a355b4d00ab31f92/deki/services/default/28','SVG',1,1,'','2011-07-11 19:55:59'),(29,'EXT','sid://mindtouch.com/2007/12/dekiscript',NULL,'Syntax Highlighter',1,1,'System.Exception: unable to initialize service (async operation timed out)\n  at MindTouch.Dream.DreamService+<CreateService_Helper>d__19.MoveNext () [0x00000] in <filename unknown>:0 \n  at MindTouch.Tasking.Coroutine.Continue () [0x00000] in <filename unknown>:0 \n   --- End of exception stack trace ---\n   at MindTouch.Dream.DreamService.CreateService_Helper(String path, String sid, XDoc config, Result`1 result)\n   --- End of coroutine stack trace ---','2011-07-11 19:55:59'),(30,'ext','sid://mindtouch.com/2008/02/trac',NULL,'Trac',1,0,NULL,'2011-07-11 19:55:59'),(31,'EXT','sid://mindtouch.com/2007/12/dekiscript',NULL,'Twitter',1,1,'System.Exception: unable to initialize service (async operation timed out)\n  at MindTouch.Dream.DreamService+<CreateService_Helper>d__19.MoveNext () [0x00000] in <filename unknown>:0 \n  at MindTouch.Tasking.Coroutine.Continue () [0x00000] in <filename unknown>:0 \n   --- End of exception stack trace ---\n   at MindTouch.Dream.DreamService.CreateService_Helper(String path, String sid, XDoc config, Result`1 result)\n   --- End of coroutine stack trace ---','2011-07-11 19:55:59'),(32,'EXT','sid://mindtouch.com/2007/12/dekiscript',NULL,'WidgetBox',1,1,'System.Exception: unable to initialize service (async operation timed out)\n  at MindTouch.Dream.DreamService+<CreateService_Helper>d__19.MoveNext () [0x00000] in <filename unknown>:0 \n  at MindTouch.Tasking.Coroutine.Continue () [0x00000] in <filename unknown>:0 \n   --- End of exception stack trace ---\n   at MindTouch.Dream.DreamService.CreateService_Helper(String path, String sid, XDoc config, Result`1 result)\n   --- End of coroutine stack trace ---','2011-07-11 19:55:59'),(33,'EXT','sid://mindtouch.com/2007/07/windows.live','local://4b8285ae06f9bb86a355b4d00ab31f92/deki/services/default/33','Windows Live',1,1,'','2011-07-11 19:55:59'),(35,'EXT','sid://mindtouch.com/2007/12/dekiscript',NULL,'YUI Media Player',1,1,'System.Exception: unable to initialize service (async operation timed out)\n  at MindTouch.Dream.DreamService+<CreateService_Helper>d__19.MoveNext () [0x00000] in <filename unknown>:0 \n  at MindTouch.Tasking.Coroutine.Continue () [0x00000] in <filename unknown>:0 \n   --- End of exception stack trace ---\n   at MindTouch.Dream.DreamService.CreateService_Helper(String path, String sid, XDoc config, Result`1 result)\n   --- End of coroutine stack trace ---','2011-07-11 19:55:59'),(37,'EXT','sid://mindtouch.com/2007/12/dekiscript',NULL,'Lightbox',1,1,'System.Exception: unable to initialize service (async operation timed out)\n  at MindTouch.Dream.DreamService+<CreateService_Helper>d__19.MoveNext () [0x00000] in <filename unknown>:0 \n  at MindTouch.Tasking.Coroutine.Continue () [0x00000] in <filename unknown>:0 \n   --- End of exception stack trace ---\n   at MindTouch.Dream.DreamService.CreateService_Helper(String path, String sid, XDoc config, Result`1 result)\n   --- End of coroutine stack trace ---','2011-07-11 19:55:59'),(38,'EXT','sid://mindtouch.com/2007/12/dekiscript',NULL,'Quicktime',1,1,'System.Exception: unable to initialize service (async operation timed out)\n  at MindTouch.Dream.DreamService+<CreateService_Helper>d__19.MoveNext () [0x00000] in <filename unknown>:0 \n  at MindTouch.Tasking.Coroutine.Continue () [0x00000] in <filename unknown>:0 \n   --- End of exception stack trace ---\n   at MindTouch.Dream.DreamService.CreateService_Helper(String path, String sid, XDoc config, Result`1 result)\n   --- End of coroutine stack trace ---','2011-07-11 19:55:59'),(39,'EXT','sid://mindtouch.com/2007/12/dekiscript',NULL,'Remember The Milk',1,1,'System.Exception: unable to initialize service (async operation timed out)\n  at MindTouch.Dream.DreamService+<CreateService_Helper>d__19.MoveNext () [0x00000] in <filename unknown>:0 \n  at MindTouch.Tasking.Coroutine.Continue () [0x00000] in <filename unknown>:0 \n   --- End of exception stack trace ---\n   at MindTouch.Dream.DreamService.CreateService_Helper(String path, String sid, XDoc config, Result`1 result)\n   --- End of coroutine stack trace ---','2011-07-11 19:55:59'),(40,'EXT','sid://mindtouch.com/2007/12/dekiscript',NULL,'Zoho',1,1,'System.Exception: unable to initialize service (async operation timed out)\n  at MindTouch.Dream.DreamService+<CreateService_Helper>d__19.MoveNext () [0x00000] in <filename unknown>:0 \n  at MindTouch.Tasking.Coroutine.Continue () [0x00000] in <filename unknown>:0 \n   --- End of exception stack trace ---\n   at MindTouch.Dream.DreamService.CreateService_Helper(String path, String sid, XDoc config, Result`1 result)\n   --- End of coroutine stack trace ---','2011-07-11 19:55:59'),(41,'ext','sid://mindtouch.com/ent/2008/05/salesforce',NULL,'Salesforce',1,0,NULL,'2011-07-11 19:55:59'),(42,'ext','sid://mindtouch.com/ent/2008/05/sugarcrm',NULL,'SugarCRM',1,0,NULL,'2011-07-11 19:55:59'),(43,'ext','sid://mindtouch.com/ext/2009/12/anychart',NULL,'AnyChart',1,0,NULL,'2011-07-11 19:55:59'),(44,'ext','sid://mindtouch.com/ext/2009/12/anygantt',NULL,'AnyGantt',1,0,NULL,'2011-07-11 19:55:59'),(20,'EXT','sid://mindtouch.com/2007/12/dekiscript',NULL,'PageBus',1,1,'System.Exception: unable to initialize service (async operation timed out)\n  at MindTouch.Dream.DreamService+<CreateService_Helper>d__19.MoveNext () [0x00000] in <filename unknown>:0 \n  at MindTouch.Tasking.Coroutine.Continue () [0x00000] in <filename unknown>:0 \n   --- End of exception stack trace ---\n   at MindTouch.Dream.DreamService.CreateService_Helper(String path, String sid, XDoc config, Result`1 result)\n   --- End of coroutine stack trace ---','2011-07-11 19:55:59'),(5,'EXT','sid://mindtouch.com/2007/12/dekiscript',NULL,'DHtml',1,1,'System.Exception: unable to initialize service (async operation timed out)\n  at MindTouch.Dream.DreamService+<CreateService_Helper>d__19.MoveNext () [0x00000] in <filename unknown>:0 \n  at MindTouch.Tasking.Coroutine.Continue () [0x00000] in <filename unknown>:0 \n   --- End of exception stack trace ---\n   at MindTouch.Dream.DreamService.CreateService_Helper(String path, String sid, XDoc config, Result`1 result)\n   --- End of coroutine stack trace ---','2011-07-11 19:55:59'),(34,'EXT','sid://mindtouch.com/2007/06/yahoo','local://4b8285ae06f9bb86a355b4d00ab31f92/deki/services/default/34','Yahoo!',1,1,'','2011-07-11 19:55:59'),(36,'EXT','sid://mindtouch.com/2007/12/dekiscript',NULL,'EditGrid',1,1,'System.Exception: unable to initialize service (async operation timed out)\n  at MindTouch.Dream.DreamService+<CreateService_Helper>d__19.MoveNext () [0x00000] in <filename unknown>:0 \n  at MindTouch.Tasking.Coroutine.Continue () [0x00000] in <filename unknown>:0 \n   --- End of exception stack trace ---\n   at MindTouch.Dream.DreamService.CreateService_Helper(String path, String sid, XDoc config, Result`1 result)\n   --- End of coroutine stack trace ---','2011-07-11 19:55:59');
/*!40000 ALTER TABLE `services` ENABLE KEYS */;
UNLOCK TABLES;

-- De-anonymize the Admin user
UPDATE `users` 
SET user_name='Admin',
    user_real_name='Admin',
    user_password='77da245e656a56818e6d7d874e1dd5c7',
    user_email='lorchard@mozilla.com',
    user_touched='20110711201719',
    user_token='2158a249b6b8368a738bf81d97627be1',
    user_role_id=5,
    user_active=1,
    user_external_name=NULL,
    user_service_id=1,
    user_builtin=1,
    user_create_timestamp='0001-01-01 00:00:00'
WHERE user_id=10611;

-- User ID 115908 is apparently the Anonymous user in current data dumps
UPDATE `users` 
SET user_name='Anonymous',
    user_real_name='Anonymous',
    user_password='',
    user_email='',
    user_touched='20110711201719',
    user_token='2158a249b6b8368a738bf81d97627be1',
    user_role_id=3,
    user_active=1,
    user_external_name=NULL,
    user_service_id=1,
    user_builtin=1,
    user_create_timestamp='0001-01-01 00:00:00'
WHERE user_id=115908;
