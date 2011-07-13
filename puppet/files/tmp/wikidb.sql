-- MySQL dump 10.11
--
-- Host: localhost    Database: wikidb
-- ------------------------------------------------------
-- Server version	5.0.77-log

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `archive`
--

DROP TABLE IF EXISTS `archive`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `archive` (
  `ar_id` int(4) unsigned NOT NULL auto_increment,
  `ar_namespace` tinyint(2) unsigned NOT NULL default '0',
  `ar_title` varchar(255) NOT NULL default '',
  `ar_text` mediumtext NOT NULL,
  `ar_comment` tinyblob NOT NULL,
  `ar_user` int(5) unsigned NOT NULL default '0',
  `ar_timestamp` varchar(14) NOT NULL default '',
  `ar_minor_edit` tinyint(1) NOT NULL default '0',
  `ar_last_page_id` int(8) unsigned NOT NULL default '0',
  `ar_old_id` int(8) unsigned NOT NULL default '0',
  `ar_flags` tinyblob NOT NULL,
  `ar_content_type` varchar(255) NOT NULL default 'application/x.deki-text',
  `ar_language` varchar(10) NOT NULL default '',
  `ar_display_name` varchar(255) default NULL,
  `ar_transaction_id` int(4) unsigned NOT NULL default '0',
  `ar_is_hidden` tinyint(3) unsigned NOT NULL default '0',
  `ar_meta` text,
  PRIMARY KEY  (`ar_id`),
  KEY `name_title_timestamp` (`ar_namespace`,`ar_title`,`ar_timestamp`),
  KEY `ar_last_page_id` (`ar_last_page_id`),
  KEY `ar_transaction_id` (`ar_transaction_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `archive`
--

LOCK TABLES `archive` WRITE;
/*!40000 ALTER TABLE `archive` DISABLE KEYS */;
/*!40000 ALTER TABLE `archive` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `banips`
--

DROP TABLE IF EXISTS `banips`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `banips` (
  `banip_id` int(10) unsigned NOT NULL auto_increment,
  `banip_ipaddress` varchar(15) default NULL,
  `banip_ban_id` int(4) unsigned NOT NULL,
  PRIMARY KEY  (`banip_id`),
  KEY `banip_ipaddress` (`banip_ipaddress`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `banips`
--

LOCK TABLES `banips` WRITE;
/*!40000 ALTER TABLE `banips` DISABLE KEYS */;
/*!40000 ALTER TABLE `banips` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `bans`
--

DROP TABLE IF EXISTS `bans`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `bans` (
  `ban_id` int(4) unsigned NOT NULL auto_increment,
  `ban_by_user_id` int(4) unsigned NOT NULL,
  `ban_expires` datetime default NULL,
  `ban_reason` text,
  `ban_revokemask` bigint(8) unsigned NOT NULL,
  `ban_last_edit` datetime default NULL,
  PRIMARY KEY  (`ban_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `bans`
--

LOCK TABLES `bans` WRITE;
/*!40000 ALTER TABLE `bans` DISABLE KEYS */;
/*!40000 ALTER TABLE `bans` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `banusers`
--

DROP TABLE IF EXISTS `banusers`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `banusers` (
  `banuser_id` int(4) unsigned NOT NULL auto_increment,
  `banuser_user_id` int(4) unsigned NOT NULL,
  `banuser_ban_id` int(4) unsigned NOT NULL,
  UNIQUE KEY `banuser_id` (`banuser_id`),
  KEY `banuser_user_id` (`banuser_user_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `banusers`
--

LOCK TABLES `banusers` WRITE;
/*!40000 ALTER TABLE `banusers` DISABLE KEYS */;
/*!40000 ALTER TABLE `banusers` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `brokenlinks`
--

DROP TABLE IF EXISTS `brokenlinks`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `brokenlinks` (
  `bl_from` int(8) unsigned NOT NULL default '0',
  `bl_to` varchar(255) NOT NULL default '',
  UNIQUE KEY `bl_from` (`bl_from`,`bl_to`),
  KEY `bl_to` (`bl_to`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `brokenlinks`
--

LOCK TABLES `brokenlinks` WRITE;
/*!40000 ALTER TABLE `brokenlinks` DISABLE KEYS */;
/*!40000 ALTER TABLE `brokenlinks` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `comments`
--

DROP TABLE IF EXISTS `comments`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `comments` (
  `cmnt_id` int(8) unsigned NOT NULL auto_increment,
  `cmnt_page_id` int(8) unsigned NOT NULL,
  `cmnt_number` int(2) unsigned NOT NULL,
  `cmnt_poster_user_id` int(4) unsigned NOT NULL,
  `cmnt_create_date` timestamp NOT NULL default CURRENT_TIMESTAMP,
  `cmnt_last_edit` timestamp NULL default NULL,
  `cmnt_last_edit_user_id` int(4) unsigned default NULL,
  `cmnt_content` text NOT NULL,
  `cmnt_content_mimetype` varchar(25) NOT NULL,
  `cmnt_title` varchar(50) default NULL,
  `cmnt_deleter_user_id` int(8) unsigned default NULL,
  `cmnt_delete_date` timestamp NULL default NULL,
  PRIMARY KEY  (`cmnt_id`),
  UNIQUE KEY `pageid_number` (`cmnt_page_id`,`cmnt_number`),
  KEY `cmnt_poster_user_id` (`cmnt_poster_user_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `comments`
--

LOCK TABLES `comments` WRITE;
/*!40000 ALTER TABLE `comments` DISABLE KEYS */;
/*!40000 ALTER TABLE `comments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `config`
--

DROP TABLE IF EXISTS `config`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `config` (
  `config_id` int(10) unsigned NOT NULL auto_increment,
  `config_key` varchar(255) NOT NULL,
  `config_value` text NOT NULL,
  PRIMARY KEY  (`config_id`),
  KEY `config_key` (`config_key`)
) ENGINE=MyISAM AUTO_INCREMENT=76 DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `config`
--

LOCK TABLES `config` WRITE;
/*!40000 ALTER TABLE `config` DISABLE KEYS */;
INSERT INTO `config` VALUES (30,'@id','default'),(31,'admin',''),(32,'admin/email','lorchard@mozilla.com'),(33,'cache',''),(34,'cache/master','request'),(35,'db-catalog','wikidb'),(36,'db-options','pooling=true; Connection Timeout=5; Connection Lifetime=30; Protocol=socket; Min Pool Size=2; Max Pool Size=50; Connection Reset=false;character set=utf8;ProcedureCacheSize=25;Use Procedure Bodies=true;'),(37,'db-port','3306'),(38,'db-server','localhost'),(39,'db-user','wikiuser'),(40,'editor',''),(41,'editor/safe-html','true'),(42,'files',''),(43,'files/blacklisted-disposition-mimetypes',''),(44,'files/blocked-extensions','html, htm, exe, vbs, scr, reg, bat, com, htm, html, xhtml'),(45,'files/force-text-extensions','htm, html, xhtml, bat, reg, sh'),(46,'files/imagemagick-extensions','bmp, jpg, jpeg, png, gif'),(47,'files/imagemagick-max-size','2000000'),(48,'files/max-file-size','268435456'),(49,'files/whitelisted-disposition-mimetypes','text/plain, text/xml, application/xml, application/pdf, application/msword, application/vnd.ms-excel, application/vnd.ms-powerpoint, application/vnd.openxmlformats-officedocument.wordprocessingml.document, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.openxmlformats-officedocument.presentationml.presentation, application/vnd.oasis.opendocument.presentation, application/vnd.oasis.opendocument.spreadsheet, application/vnd.oasis.opendocument.text, application/x-shockwave-flash'),(50,'host','*'),(51,'languages',''),(52,'license',''),(53,'security',''),(54,'security/admin-user-for-impersonation','Admin'),(55,'security/allow-anon-account-creation','true'),(56,'security/api-key','GFxaNVK37fLPsFEYM7NwdIuNpGIiFTOX'),(57,'security/cookie-expire-secs','604800'),(58,'security/new-account-role','Contributor'),(59,'storage',''),(60,'storage/fs',''),(61,'storage/fs/path','/var/www/dekiwiki/attachments'),(62,'storage/s3',''),(63,'storage/s3/bucket',''),(64,'storage/s3/prefix',''),(65,'storage/s3/privatekey',''),(66,'storage/s3/publickey',''),(67,'storage/s3/timeout',''),(68,'storage/type','fs'),(69,'ui',''),(70,'ui/analytics-key','UA-68075-16'),(71,'ui/banned-words',''),(72,'ui/language','en-us'),(73,'ui/sitename','MDN'),(74,'ui/skin','Transitional'),(75,'ui/template','mdn');
/*!40000 ALTER TABLE `config` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `group_grants`
--

DROP TABLE IF EXISTS `group_grants`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `group_grants` (
  `group_grant_id` int(10) unsigned NOT NULL auto_increment,
  `page_id` int(10) unsigned NOT NULL,
  `group_id` int(10) unsigned NOT NULL,
  `role_id` int(4) unsigned NOT NULL,
  `creator_user_id` int(10) unsigned NOT NULL,
  `expire_date` datetime default NULL,
  `last_edit` timestamp NOT NULL default CURRENT_TIMESTAMP on update CURRENT_TIMESTAMP,
  PRIMARY KEY  (`group_grant_id`),
  UNIQUE KEY `page_id` (`page_id`,`group_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `group_grants`
--

LOCK TABLES `group_grants` WRITE;
/*!40000 ALTER TABLE `group_grants` DISABLE KEYS */;
/*!40000 ALTER TABLE `group_grants` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `groups`
--

DROP TABLE IF EXISTS `groups`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `groups` (
  `group_id` int(10) unsigned NOT NULL auto_increment,
  `group_name` varchar(255) NOT NULL,
  `group_role_id` int(4) unsigned NOT NULL,
  `group_service_id` int(4) unsigned NOT NULL,
  `group_creator_user_id` int(10) unsigned NOT NULL default '0',
  `group_last_edit` timestamp NOT NULL default CURRENT_TIMESTAMP on update CURRENT_TIMESTAMP,
  PRIMARY KEY  (`group_id`),
  UNIQUE KEY `group_name` (`group_name`,`group_service_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `groups`
--

LOCK TABLES `groups` WRITE;
/*!40000 ALTER TABLE `groups` DISABLE KEYS */;
/*!40000 ALTER TABLE `groups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `links`
--

DROP TABLE IF EXISTS `links`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `links` (
  `l_from` int(8) unsigned NOT NULL default '0',
  `l_to` int(8) unsigned NOT NULL default '0',
  UNIQUE KEY `l_from` (`l_from`,`l_to`),
  KEY `l_to` (`l_to`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `links`
--

LOCK TABLES `links` WRITE;
/*!40000 ALTER TABLE `links` DISABLE KEYS */;
/*!40000 ALTER TABLE `links` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `linkscc`
--

DROP TABLE IF EXISTS `linkscc`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `linkscc` (
  `lcc_pageid` int(10) unsigned NOT NULL default '0',
  `lcc_cacheobj` mediumblob NOT NULL,
  UNIQUE KEY `lcc_pageid` (`lcc_pageid`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `linkscc`
--

LOCK TABLES `linkscc` WRITE;
/*!40000 ALTER TABLE `linkscc` DISABLE KEYS */;
/*!40000 ALTER TABLE `linkscc` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `objectcache`
--

DROP TABLE IF EXISTS `objectcache`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `objectcache` (
  `keyname` varchar(255) NOT NULL default '',
  `value` mediumblob,
  `exptime` datetime default NULL,
  UNIQUE KEY `keyname` (`keyname`),
  KEY `exptime` (`exptime`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `objectcache`
--

LOCK TABLES `objectcache` WRITE;
/*!40000 ALTER TABLE `objectcache` DISABLE KEYS */;
/*!40000 ALTER TABLE `objectcache` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `old`
--

DROP TABLE IF EXISTS `old`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `old` (
  `old_id` int(8) unsigned NOT NULL auto_increment,
  `old_namespace` tinyint(2) unsigned NOT NULL default '0',
  `old_title` varchar(255) NOT NULL default '',
  `old_text` mediumtext NOT NULL,
  `old_comment` tinyblob NOT NULL,
  `old_user` int(5) unsigned NOT NULL default '0',
  `old_timestamp` varchar(14) NOT NULL default '',
  `old_minor_edit` tinyint(1) NOT NULL default '0',
  `old_flags` tinyblob NOT NULL,
  `old_content_type` varchar(255) NOT NULL default 'application/x.deki-text',
  `old_language` varchar(10) NOT NULL default '',
  `old_display_name` varchar(255) default NULL,
  `inverse_timestamp` varchar(14) NOT NULL default '',
  `old_is_hidden` tinyint(3) unsigned NOT NULL default '0',
  `old_meta` text,
  PRIMARY KEY  (`old_id`),
  KEY `old_timestamp` (`old_timestamp`),
  KEY `name_title_timestamp` (`old_namespace`,`old_title`,`inverse_timestamp`),
  KEY `user_timestamp` (`old_user`,`inverse_timestamp`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `old`
--

LOCK TABLES `old` WRITE;
/*!40000 ALTER TABLE `old` DISABLE KEYS */;
/*!40000 ALTER TABLE `old` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `pages`
--

DROP TABLE IF EXISTS `pages`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `pages` (
  `page_id` int(8) unsigned NOT NULL auto_increment,
  `page_namespace` tinyint(2) unsigned NOT NULL default '0',
  `page_title` varchar(255) NOT NULL,
  `page_text` mediumtext NOT NULL,
  `page_comment` blob NOT NULL,
  `page_user_id` int(10) unsigned NOT NULL default '0',
  `page_timestamp` varchar(14) NOT NULL,
  `page_counter` bigint(20) unsigned NOT NULL default '0',
  `page_is_redirect` tinyint(1) unsigned NOT NULL default '0',
  `page_minor_edit` tinyint(1) unsigned NOT NULL default '0',
  `page_is_new` tinyint(1) unsigned NOT NULL default '0',
  `page_random` double unsigned NOT NULL default '0',
  `page_touched` varchar(14) NOT NULL,
  `page_inverse_timestamp` varchar(14) NOT NULL,
  `page_usecache` tinyint(1) unsigned NOT NULL default '1',
  `page_toc` blob NOT NULL,
  `page_tip` text NOT NULL,
  `page_parent` int(8) NOT NULL default '0',
  `page_restriction_id` int(4) unsigned NOT NULL,
  `page_content_type` varchar(255) NOT NULL default 'application/x.deki-text',
  `page_language` varchar(10) NOT NULL default '',
  `page_display_name` varchar(255) default NULL,
  `page_template_id` int(8) unsigned default NULL,
  `page_is_hidden` tinyint(3) unsigned NOT NULL default '0',
  `page_meta` text,
  PRIMARY KEY  (`page_id`),
  UNIQUE KEY `name_title` (`page_namespace`,`page_title`),
  KEY `page_title` (`page_title`(20)),
  KEY `page_timestamp` (`page_timestamp`),
  KEY `page_random` (`page_random`),
  KEY `page_parent` (`page_parent`),
  KEY `name_title_timestamp` (`page_namespace`,`page_title`,`page_inverse_timestamp`),
  KEY `user_timestamp` (`page_user_id`,`page_inverse_timestamp`),
  KEY `usertext_timestamp` (`page_inverse_timestamp`),
  KEY `namespace_redirect_timestamp` (`page_namespace`,`page_is_redirect`,`page_timestamp`)
) ENGINE=MyISAM AUTO_INCREMENT=39 DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `pages`
--

LOCK TABLES `pages` WRITE;
/*!40000 ALTER TABLE `pages` DISABLE KEYS */;
INSERT INTO `pages` VALUES (1,101,'Userlogin','','',0,'',0,0,0,0,0,'','',1,'','Special page',0,0,'text/plain','',NULL,NULL,0,NULL),(2,101,'Userlogout','','',0,'',0,0,0,0,0,'','',1,'','Special page',0,0,'text/plain','',NULL,NULL,0,NULL),(3,101,'Preferences','','',0,'',0,0,0,0,0,'','',1,'','Special page',0,0,'text/plain','',NULL,NULL,0,NULL),(4,101,'Watchedpages','','',0,'',0,0,0,0,0,'','',1,'','Special page',0,0,'text/plain','',NULL,NULL,0,NULL),(5,101,'Recentchanges','','',0,'',0,0,0,0,0,'','',1,'','Special page',0,0,'text/plain','',NULL,NULL,0,NULL),(6,101,'Listusers','','',0,'',0,0,0,0,0,'','',1,'','Special page',0,0,'text/plain','',NULL,NULL,0,NULL),(7,101,'ListTemplates','','',0,'',0,0,0,0,0,'','',1,'','Special page',0,0,'text/plain','',NULL,NULL,0,NULL),(8,101,'ListRss','','',0,'',0,0,0,0,0,'','',1,'','Special page',0,0,'text/plain','',NULL,NULL,0,NULL),(9,101,'Search','','',0,'',0,0,0,0,0,'','',1,'','Special page',0,0,'text/plain','',NULL,NULL,0,NULL),(10,101,'Sitemap','','',0,'',0,0,0,0,0,'','',1,'','Special page',0,0,'text/plain','',NULL,NULL,0,NULL),(11,101,'Contributions','','',0,'',0,0,0,0,0,'','',1,'','Special page',0,0,'text/plain','',NULL,NULL,0,NULL),(12,101,'Undelete','','',0,'',0,0,0,0,0,'','',1,'','Special page',0,0,'text/plain','',NULL,NULL,0,NULL),(13,101,'Popularpages','','',0,'',0,0,0,0,0,'','',1,'','Special page',0,0,'text/plain','',NULL,NULL,0,NULL),(14,101,'Watchlist','','',0,'',0,0,0,0,0,'','',1,'','Special page',0,0,'text/plain','',NULL,NULL,0,NULL),(15,101,'About','','',0,'',0,0,0,0,0,'','',1,'','Special page',0,0,'text/plain','',NULL,NULL,0,NULL),(16,101,'Statistics','','',0,'',0,0,0,0,0,'','',1,'','Special page',0,0,'text/plain','',NULL,NULL,0,NULL),(17,101,'Tags','','',0,'',0,0,0,0,0,'','',1,'','Special page',0,0,'text/plain','',NULL,NULL,0,NULL),(18,101,'Events','','',0,'',0,0,0,0,0,'','',1,'','Special page',0,0,'text/plain','',NULL,NULL,0,NULL),(19,2,'','User page','',0,'',0,0,0,0,0,'','',1,'','Admin page',0,0,'text/plain','',NULL,NULL,0,NULL),(20,10,'','','',0,'',0,0,0,0,0,'','',1,'','Template page',0,0,'text/plain','',NULL,NULL,0,NULL),(21,10,'MindTouch_UserWelcome','<pre class=\"script\">\r\n // check if user is looking at their own page\r\n if (wiki.getuser(user.id).uri == page.uri) {\r\n &lt;style type=&quot;text/css&quot;&gt;&quot;\r\n #user-welcome h2 {\r\n font-family: Arial, sans-serif;\r\n border: none;\r\n color: #454545;\r\n font-size: 25px;\r\n font-weight: normal;\r\n line-height: 30px;\r\n margin: 20px 0;\r\n }\r\n #user-welcome h4 {\r\n font-family: Verdana, Arial, Helvetica, sans-serif;\r\n font-size: 18px;\r\n line-height: 28px;\r\n margin-bottom: 10px;\r\n margin-top: 0;\r\n color: #454545;\r\n }\r\n #user-welcome .share {\r\n font-weight: bold;\r\n font-size: 14px;\r\n line-height: 20px;\r\n color: #666666;\r\n }\r\n #user-welcome-header {\r\n border: 2px solid #c4e1ed;\r\n background: #d1e8f0 url(/skins/common/images/oobe/mt-bg-user-welcome.png) repeat-x scroll center top;\r\n margin-top: 20px;\r\n padding: 25px;\r\n }\r\n #user-welcome-signup {\r\n font-family:Arial, Helvetica, sans-serif;\r\n margin: 0;\r\n pad ding: 35px 40px 20px 40px;\r\n font-size: 18px;\r\n line-height: 28px;\r\n }\r\n #user-welcome-signup a {\r\n color: #bc0d0d;\r\n }\r\n #user-welcome-signup a:hover {\r\n color: #d70808;\r\n }\r\n #user-welcome-more {\r\n padding: 25px;\r\n }\r\n #user-welcome ul li {\r\n padding: 0;\r\n margin: 0 0 14px;\r\n }\r\n &quot;&lt;/style&gt;\r\n \r\n &lt;div id=&quot;user-welcome&quot;&gt;\r\n &lt;h2&gt;\r\n wiki.localize(\'MindTouch.Templates.userwelcome\', [site.name]);\r\n &lt;/h2&gt;\r\n &lt;p class=&quot;share&quot;&gt;\r\n wiki.localize(\'System.API.new-user-page-text\');\r\n &lt;/p&gt;\r\n &lt;div id=&quot;user-welcome-header&quot;&gt;\r\n &lt;p id=&quot;user-welcome-signup&quot;&gt;\r\n &lt;a href=(&quot;http://www.mindtouch.com/MindTouchU_signup&quot; &amp; {\r\n email: user.email,\r\n lang: wiki.language(),\r\n signup: &quot;yes&quot;\r\n })\r\n title=(wiki.localize(\'MindTouch.Templates.UserWelcome.signup.link\'))&gt;\r\n wiki.localize(\'MindTouch.Templates.userwelcome.signup.link\')              &lt;/a&gt;\r\n wiki.localize(\'MindTouch.Templates.userwelcome.signup\');\r\n &lt;/p&gt;\r\n &lt;/div&gt;\r\n \r\n &lt;div id=&quot;user-welcome-more&quot;&gt;\r\n &lt;h4&gt;\r\n wiki.localize(\'MindTouch.Templates.userwelcome.more\');\r\n &lt;/h4&gt;\r\n &lt;ul&gt;\r\n &lt;li&gt;\r\n &lt;a href=(&quot;http://www.mindtouch.com/u_video&quot; &amp; {\r\n email: user.email,\r\n lang: wiki.language()\r\n })\r\n title=(wiki.localize(\'MindTouch.Templates.UserWelcome.getting-started\'))&gt;\r\n wiki.localize(\'MindTouch.Templates.UserWelcome.getting-started\');\r\n &lt;/a&gt;\r\n &lt;/li&gt;\r\n &lt;li&gt;\r\n &lt;a href=(&quot;http://www.mindtouch.com/u_webinar&quot; &amp; {                     email: user.email,\r\n lang: wiki.language()\r\n })\r\n title=(wiki.localize(\'MindTouch.Templates.UserWelcome.free-webinar\'))&gt;\r\n wiki.localize(\'MindTouch.Templates.UserWelcome.free-webinar\');\r\n &lt;/a&gt;\r\n &lt;/li&gt;\r\n &lt;/ul&gt;\r\n &lt;/div&gt;\r\n &lt;/div&gt;\r\n } else {\r\n // displayed for visitors to the user page\r\n wiki.localize(\'MindTouch.Templates.UserWelcome.visitor\');\r\n }\r\n </pre> ','',1,'20071103195811',0,0,0,0,0,'0','79928896804188',1,'','',0,0,'application/x.deki-text','',NULL,NULL,0,NULL),(22,0,'','<h2>Welcome to MindTouch</h2><pre class=\"script\">if (user.admin) {	mt_admin_tabs();} else {	mt_user_tabs(); } </pre>','',1,'20071103195811',0,0,0,0,0,'0','79928896804188',1,'','',0,0,'application/x.deki-text','',NULL,NULL,0,NULL),(23,10,'mt_admin_extranet','<div class=\"mt-title-bar mt-title-bar-admin-extranet\">{{mt_license();}}&nbsp;</div> <div class=\"mt-table\"> <ul> <li> <div> <h4>Identify Your Extranet</h4> <h5>Customer extranet (public)</h5> <p>A customer extranet portal is a secure website that enables businesses to share documents, communicate and share content with customers in a central repository. The customer extranet portal provides access to collaborative tools with just an Internet connection.</p> <h5>Partner extranet (private)</h5> <p>The partner extranet portal is a private website that enables businesses to share content with partners in a secure environment. The partner extranet portal provides data connections with CRM as well as collaborative tools with just an Internet connection.</p> </div> </li> <li class=\"middle\"> <div> <h4>Sharing Official Documentation</h4> <p>Creating new content makes your documentation richer and more valuable. Use the <strong>{{wiki.create{label:\"New page\", title:\"New page created by \"..user.name, button:false}}}</strong> link to add a page or use the <strong>Edit page</strong> link to make changes to an existing page.</p> <p>File management is simple, manageable and files are versioned with each modification.</p> <p class=\"mt-btn-bar mt-btn-create-page\">{{wiki.create{label:\"create a new page\", title:\"New page created by \"..user.name, button:false}}}</p> <h4>Stay Informed</h4> <p>Monitoring your extranet with MindTouch has never been easier. With page notifications you can receive edit overview emails when any or all pages are modified. Look for the <img style=\"vertical-align:top;\" alt=\"\" src=\"/skins/common/images/oobe/mt-icon-notifications.gif\" /> icon on each page.</p> </div> </li> <li> <div> <h4>User / Role Management</h4> <p>User management with MindTouch is easy, extensive and versatile. Create new <a title=\"deki/cp/user_management.php\" class=\"mt-cp-link\" href=\"/deki/cp/user_management.php\">users</a>, <a title=\"deki/cp/role_management.php\" class=\"mt-cp-link\" href=\"/deki/cp/role_management.php\">roles</a> and <a title=\"deki/cp/group_management.php\" class=\"mt-cp-link\" href=\"/deki/cp/group_management.php\">groups</a> in the <a title=\"deki/cp/dashboard.php\" class=\"mt-cp-link\" href=\"/deki/cp/dashboard.php\">control panel</a>.</p> <p class=\"mt-btn-bar mt-btn-user-page\"><a title=\"deki/cp/user_management.php\" href=\"/deki/cp/user_management.php\">user manager</a></p> <h4>Permissions and Privacy</h4> <p>Need to keep something to yourself? Privacy with MindTouch is easy and secure.</p> <ol class=\"mt-small\"> <li>Go to the page you wish to protect</li> <li>Click <strong>More &gt; Restrict Access</strong></li> <li>Select the appropriate restriction level</li> </ol> <p style=\"text-align:center; margin:0\"><img alt=\"\" src=\"/skins/common/images/oobe/mt-img-privacy-settings.gif\" /></p> </div> </li> </ul> </div> <p style=\"margin:3px 0;text-align:right;padding-right:30px;\"><img alt=\"\" src=\"/skins/common/images/oobe/mt-img-privacy-legend.gif\" /></p>','',1,'20071103195811',0,0,0,0,0,'0','79928896804188',1,'','',0,0,'application/x.deki-text','',NULL,NULL,0,NULL),(24,10,'mt_admin_intranet','<div class=\"mt-title-bar mt-title-bar-admin-intranet\"> <div><a class=\"mt-tips external\" href=\"http://www.mindtouch.com/Solutions/Intranet_Solution\">Did you know that MindTouch has out of the box <strong>Collaborative Intranets</strong>?</a></div> &nbsp;</div> <div class=\"mt-table\"> <ul> <li> <div> <h4>What makes a good Intranet?</h4> <p>MindTouch Intranets tightly integrate projects, content management, teams and search into a single <a href=\"http://www.mindtouch.com/Solutions/Intranet_Solution\">out of the box intranet solution</a>.</p> <h4>MindTouch Intranet</h4> <p style=\"text-align:center;\"><img alt=\"\" src=\"/skins/common/images/oobe/mt-img-intranet.gif\" /></p> <p>Leverage user contributions to build your intranet and establish community champions.</p> </div> </li> <li class=\"middle\"> <div> <h4>Authentication</h4> <p>Authentication with MindTouch is flexible and powerful.  MindTouch enables you to leverage your existing authentication providers such as LDAP/AD for a seamless <strong>single-sign-on</strong> experience.</p> <p></p> <p class=\"mt-btn-bar mt-btn-authentication\"><a title=\"deki/cp/authentication.php\" href=\"/deki/cp/authentication.php\">add authentication</a></p> <h4>Intranet Setup</h4> <p>Setting up your intranet is a snap. Set up team and department pages, dashboards and projects with just a few clicks.</p> <p>Use MindTouch permissions to grant users access to specific hierarchies.</p> </div> </li> <li> <div> <h4>User / Role Management</h4> <p>User management with MindTouch is easy, extensive and versatile. Create new <a class=\"mt-cp-link\" title=\"deki/cp/user_management.php\" href=\"/deki/cp/user_management.php\">users</a>, <a class=\"mt-cp-link\" title=\"deki/cp/role_management.php\" href=\"/deki/cp/role_management.php\">roles</a> and <a class=\"mt-cp-link\" title=\"deki/cp/group_management.php\" href=\"/deki/cp/group_management.php\">groups</a> in the <a class=\"mt-cp-link\" title=\"deki/cp/dashboard.php\" href=\"/deki/cp/dashboard.php\">control panel</a>.</p> <p class=\"mt-btn-bar mt-btn-user-page\"><a title=\"deki/cp/user_management.php\" href=\"/deki/cp/user_management.php\">user manager</a></p> <h4>Permissions and Privacy</h4> <p>Need to keep something to yourself? Privacy with MindTouch is easy and secure.</p> <ol class=\"mt-small\"> <li>Go to the page you wish to protect</li> <li>Click <strong>More &gt; Restrict Access</strong></li> <li>Select the appropriate restriction level</li> </ol> <p style=\"text-align:center; margin:0\"><img alt=\"\" src=\"/skins/common/images/oobe/mt-img-privacy-settings.gif\" /></p> </div> </li> </ul> </div> <p style=\"margin:3px 0;text-align:right;padding-right:30px;\"><img alt=\"\" src=\"/skins/common/images/oobe/mt-img-privacy-legend.gif\" /></p>','',1,'20071103195811',0,0,0,0,0,'0','79928896804188',1,'','',0,0,'application/x.deki-text','',NULL,NULL,0,NULL),(25,10,'mt_admin_kb','<div class=\"mt-title-bar mt-title-bar-admin-kb\"> <div><a class=\"mt-tips external\" href=\"http://www.mindtouch.com/Solutions/Knowledge_Base\">Did you know that MindTouch has an out of the box <strong>Collaborative Knowledge Base</strong> solution?</a></div> &nbsp;</div> <div class=\"mt-table\"> <ul> <li> <div> <h4>Knowledge Base Templates</h4> <p>Create your own templates or use the default templates below. You can add templates by clicking <img style=\"vertical-align:middle;\" alt=\"\" src=\"/skins/common/images/oobe/mt-icon-template.gif\" /> while editing.</p> <div class=\"mt-template-row\"><img alt=\"\" src=\"/skins/common/images/oobe/mt-button-template-left-bar.gif\" /> <span class=\"mt-template-title\">Left Highlight</span> {{wiki.create{label:\"Create a new page with a left highlight layout\", template:\"mt_template_left_highlight\", title:\"New left highlight page created by \"..user.name, button:false}}}</div> <div class=\"mt-template-row\"><img alt=\"\" src=\"/skins/common/images/oobe/mt-button-template-documentation-files.gif\" /> <span class=\"mt-template-title\">Documentation with files</span> {{wiki.create{label:\"Create a new page with a documentation and files layout\", template:\"mt_template_documentation_files\", title:\"New documentation and files page created by \"..user.name, button:false}}}</div> <div class=\"mt-template-row\"><img alt=\"\" src=\"/skins/common/images/oobe/mt-button-template-faq.gif\" /> <span class=\"mt-template-title\">Frequently Asked Quesions</span> {{wiki.create{label:\"Create a new frequently asked questions layout\", template:\"mt_template_faq\", title:\"New frequently asked questions page created by \"..user.name, button:false}}}</div> <p class=\"mt-btn-bar mt-btn-create-template\">{{wiki.create{label:\"create a template\", title:\"New template created by \"..user.name, path:\"Template:\", button:false}}}</p> </div> </li> <li class=\"middle\"> <div> <h4>Document Management</h4> <p>Keep your knowledge base organized with the <a class=\"external\" href=\"http://www.mindtouch.com/Products/Desktop_Tools\">MindTouch Desktop Connector</a>. Manage, organize and modify your knowledge base from the comfort of a desktop application.</p> <h4>Properly Identifying Content</h4> <p>MindTouch provides a number of tools to make organizing and searching your content quick and effective.</p> <ol class=\"mt-small\"> <li><strong>Tags:&nbsp;</strong>Tag your MindTouch pages to show relevant keywords and related pages.</li> <li><strong>Attachments:&nbsp;</strong>Attachments are indexed and searched for contextual relevance.</li> <li><strong>Comments:&nbsp;</strong>Add community generated content to your site to increase a pages relevancy.</li> </ol> </div> </li> <li> <div> <h4>User / Role Management</h4> <p>User management with MindTouch is easy, extensive and versatile. Create new <a class=\"mt-cp-link\" title=\"deki/cp/user_management.php\" href=\"/deki/cp/user_management.php\">users</a>, <a class=\"mt-cp-link\" title=\"deki/cp/role_management.php\" href=\"/deki/cp/role_management.php\">roles</a> and <a class=\"mt-cp-link\" title=\"deki/cp/group_management.php\" href=\"/deki/cp/group_management.php\">groups</a> in the <a class=\"mt-cp-link\" title=\"deki/cp/dashboard.php\" href=\"/deki/cp/dashboard.php\">control panel</a>.</p> <p class=\"mt-btn-bar mt-btn-user-page\"><a title=\"deki/cp/user_management.php\" href=\"/deki/cp/user_management.php\">user manager</a></p> <h4>Permissions and Privacy</h4> <p>MindTouch allows you to limit content to particular users, roles and group. You can apply limitations to individual pages or entire hierarchies.</p> <ol class=\"mt-small\"> <li>Go to the page you wish to protect</li> <li>Click <strong>More &gt; Restrict Access</strong></li> <li>Select the appropriate restriction level</li> </ol> <p style=\"text-align:center; margin:0\"><img alt=\"\" src=\"/skins/common/images/oobe/mt-img-privacy-settings.gif\" /></p> </div> </li> </ul> </div> <p style=\"margin:3px 0;text-align:right;padding-right:30px;\"><img alt=\"\" src=\"/skins/common/images/oobe/mt-img-privacy-legend.gif\" /></p> ','',1,'20071103195811',0,0,0,0,0,'0','79928896804188',1,'','',0,0,'application/x.deki-text','',NULL,NULL,0,NULL),(26,10,'mt_template_documentation_files','<div style=\"width:250px;float:right; padding:10px;background-color:#efefef; border:1px solid #ccc; margin-left:20px; min-height:500px;\"> <h2>Attached Files</h2> <ul init=\"var files = page.files\"> <li foreach=\"var file in files\">{{web.link(file.uri,file.name)}}</li> </ul> </div> <h2>Documentation Section One</h2> <p>Documentation Section One content</p> <h2>Documentation Section Two</h2> <p>Documentation Section Two content</p>','',1,'20071103195811',0,0,0,0,0,'0','79928896804188',1,'','',0,0,'application/x.deki-text','',NULL,NULL,0,NULL),(27,10,'mt_template_faq','<div style=\"width:250px;float:right; padding:10px;background-color:#efefef; border:1px solid #ccc; margin-left:20px; min-height:500px;\"> <h2>Right Highlight</h2> <p>Right highlight content.</p> </div> {{page.Toc;}} <h2>Documentation Section One</h2> <p>Documentation Section One content</p> <h2>Documentation Section Two</h2> <p>Documentation Section Two content</p>','',1,'20071103195811',0,0,0,0,0,'0','79928896804188',1,'','',0,0,'application/x.deki-text','',NULL,NULL,0,NULL),(28,10,'mt_template_left_highlight','<div style=\"width:250px;float:left; padding:10px;background-color:#efefef; border:1px solid #ccc; margin-right:20px; min-height:500px;\"> <h2>Left Highlight</h2> <p>Left highlight content.</p> </div> <h2>Main Page</h2> <p>Main page content</p>','',1,'20071103195811',0,0,0,0,0,'0','79928896804188',1,'','',0,0,'application/x.deki-text','',NULL,NULL,0,NULL),(29,10,'mt_template_right_highlight','<div style=\"width:250px;float:right; padding:10px;background-color:#efefef; border:1px solid #ccc; margin-left:20px; min-height:500px;\"> <h2>Right Highlight</h2> <p>Right highlight content.</p> </div> <h2>Main Page</h2> <p>Main page content</p>','',1,'20071103195811',0,0,0,0,0,'0','79928896804188',1,'','',0,0,'application/x.deki-text','',NULL,NULL,0,NULL),(30,10,'mt_template_three_column','<table width=\"100%\"><tr><td style=\"width:33%;\"><h2>Column one</h2><p>Column one content.</p></td><td style=\"width:33%;\"><h2>Column two</h2><p>Column two content.</p></td><td style=\"width:33%;\"><h2>Column three</h2><p>Column three content.</p></td></tr></table>','',1,'20071103195811',0,0,0,0,0,'0','79928896804188',1,'','',0,0,'application/x.deki-text','',NULL,NULL,0,NULL),(31,10,'mt_template_two_column','<table width=\"100%\"><tr><td style=\"width:50%;\"><h2>Column one</h2><p>Column one content.</p></td><td style=\"width:50%;\"><h2>Column two</h2><p>Column two content.</p></td></tr></table>','',1,'20071103195811',0,0,0,0,0,'0','79928896804188',1,'','',0,0,'application/x.deki-text','',NULL,NULL,0,NULL),(32,10,'mt_user_develop','<div class=\"mt-title-bar mt-title-bar-user-develop\">\r\n{{mt_license();}}\r\n</div>\r\n<div class=\"mt-table\">\r\n<ul>\r\n    <li>\r\n    <div>\r\n    <h4>DekiScript</h4>\r\n    <p><a class=\"external\" href=\"http://developer.mindtouch.com/DekiScript\">DekiScript</a> is the safe lightweight scripting language used for rapid application development inside MindTouch. Try this in the editor to get started:</p>\r\n    <img alt=\"\" src=\"/skins/common/images/oobe/mt-img-welcome-syntax.gif\" class=\"mt-syntax\"/>\r\n    <h4>Dynamic Templates</h4>\r\n    <p>Get started now! Use these sample to start your first DekiScript app today.</p>\r\n    <ol class=\"mt-small\">\r\n        <li><a href=\"http://developer.mindtouch.com/DekiScript/FAQ/How_do_I..._Start_writing_DekiScript%3f\" class=\"external\">Hello World</a></li>\r\n        <li><a href=\"http://developer.mindtouch.com/DekiScript/FAQ/How_do_I..._Access_user%2c_page_and_site_properties%3f\" class=\"external\">Properties: User, Page and Site</a></l i>\r\n <li><a href=\"http://developer.mindtouch.com/DekiScript/FAQ/How_do_I..._Use_the_native_DekiScript_functions%3f\" class=\"external\">Native Functions</a></li>\r\n    </ol>\r\n    <p class=\"mt-btn-bar mt-btn-create-template\" if=\"!user.anonymous\">{{wiki.create{label:\"create a template\", title:\"New template created by \"..user.name, path:\"Template:\", button:false}}}</p>\r\n    </div>\r\n    </li>\r\n    <li class=\"middle\">\r\n    <div>\r\n    <h4>API</h4>\r\n    <p>The <a class=\"external\" href=\"http://developer.mindtouch.com/Deki/API_Reference\">MindTouch API</a>&nbsp;exposes all the functionality of MindTouch through a REST-based API. Here are some sample endpoints:&nbsp;</p>\r\n    <ol class=\"mt-small\">\r\n        <li>{{web.link(site.api..\"/pages/\"..page.id,\"This page\'s XML\")}}</li>\r\n        <li>{{web.link(site.api..\"/users/\"..user.id,\"Your user\'s XML\")}}</li>\r\n        <li>{{web.link(site.api..\"/pages/popular\",\"Popular Pages XML\")}}</li>\r\n    </ol>\r\n    <p>Learn more with our&nbsp;<a class=\"external\" h ref=\"http://developer.mindtouch.com/Deki/API_Reference\">API documentation</a></p>\r\n    <h4>MindTouch Extensions</h4>\r\n    <p>Here\'s a preview of the extensions on your MindTouch:</p>\r\n    <ol class=\"mt-small\">\r\n        <li><a href=\"http://developer.mindtouch.com/Deki/Extensions/Google\" class=\"external\">Google</a></li>\r\n        <li><a href=\"http://developer.mindtouch.com/Deki/Extensions/Feed\" class=\"external\">RSS Feeds</a></li>\r\n        <li><a href=\"http://developer.mindtouch.com/Deki/Extensions/Flickr\" class=\"external\">Flickr</a></li>\r\n    </ol>\r\n    <p>You can <a class=\" external\" href=\"http://developer.mindtouch.com/Deki/Extensions\" class=\"external\">write your own extensions</a> in any language, including PHP and C#.</p>\r\n    </div>\r\n    </li>\r\n    <li>\r\n    <div>\r\n    <h4>Technical Documentation</h4>\r\n    <img alt=\"\" src=\"/skins/common/images/oobe/mt-img-syntax_highlighter.gif\" class=\"mt-syntax\"/>\r\n    <p>Using MindTouch to power your developer community? Try the <strong>Syn tax Highlighter</strong> for code samples, tutorials and more.</p>\r\n    <ol class=\"mt-small\">\r\n        <li>Paste your code into a page</li>\r\n        <li>User your mouse to select your code</li>\r\n        <li>In the toolbar, select <strong>Format &gt; Formatted</strong></li>\r\n        <li>In the toolbar, click <strong>Transformations</strong> and select your programming language</li>\r\n    </ol>\r\n    <p class=\"mt-btn-bar mt-btn-create-page\" if=\"!user.anonymous\">{{wiki.create{label:\"create a new page\", title:\"New page created by \"..user.name, button:false}}}</p>\r\n    </div>\r\n    </li>\r\n</ul>\r\n</div>','',1,'20071103195811',0,0,0,0,0,'0','79928896804188',1,'','',0,0,'application/x.deki-text','',NULL,NULL,0,NULL),(33,10,'mt_user_document','<div class=\"mt-title-bar mt-title-bar-user-document\">\r\n{{mt_license();}}\r\n</div>\r\n<div class=\"mt-table\">\r\n<ul>\r\n    <li>\r\n    <div>\r\n    <h4>Templates</h4>\r\n    <p if=\"!user.anonymous\">Create your own templates or use the default templates below. You can add templates by clicking <img style=\"vertical-align:middle;\" alt=\"\" src=\"/skins/common/images/oobe/mt-icon-template.gif\" /> while editing.</p>\r\n    <p if=\"user.anonymous\">As a registered user you can create custom layout templates to standardize the way you and other users create documentation.  For instance, you can create templates for:</p>\r\n    <ol class=\"mt-small\" if=\"user.anonymous\">\r\n    	<li>Project status reports</li>\r\n    	<li>New user instructions</li>\r\n    	<li>Development specifications</li>\r\n    	<li>Knowledge base resources</li>\r\n    	<li>Social media newsrooms</li>\r\n    </ol>\r\n    <p if=\"user.anonymous\"><a title=\"Register\" href=\"/Special:UserRegistration\">Register now</a> to start creating your own templates.</p>\r\n <p class=\"mt-btn-bar mt-btn-user-page\" if=\"user.anonymous\"><a title=\"Register\" href=\"/Special:UserRegistration\">register now</a></p>\r\n    <div class=\"mt-template-row\" if=\"!user.anonymous\"><img alt=\"\" src=\"/skins/common/images/oobe/mt-button-template-two-column.gif\" /> <span class=\"mt-template-title\">Two Column</span> {{wiki.create{label:\"Create a new page with a two column layout\", template:\"mt_template_two_column\", title:\"New two column page created by \"..user.name, button:false}}}</div>\r\n    <div class=\"mt-template-row\" if=\"!user.anonymous\"><img alt=\"\" src=\"/skins/common/images/oobe/mt-button-template-three-column.gif\" /> <span class=\"mt-template-title\">Three Column</span> {{wiki.create{label:\"Create a new page with a three column layout\", template:\"mt_template_three_column\", title:\"New three column page created by \"..user.name, button:false}}}</div>\r\n    <div class=\"mt-template-row\" if=\"!user.anonymous\"><img alt=\"\" src=\"/skins/common/images/oobe/mt-button-template-right-bar.gif\" /> <span class=\" mt-template-title\">Right Highlight</span> {{wiki.create{label:\"Create a new page with a vertical right highlight bar\", template:\"mt_template_right_highlight\", title:\"New right highlight page created by \"..user.name, button:false}}}</div>\r\n    <p class=\"mt-btn-bar mt-btn-create-template\" if=\"!user.anonymous\">{{wiki.create{label:\"create a template\", title:\"New template created by \"..user.name, path:\"Template:\", button:false}}}</p>\r\n    </div>\r\n    </li>\r\n    <li class=\"middle\">\r\n    <div>\r\n    <h4>Creating Pages</h4>\r\n    <p>Creating new content makes your documentation richer and more valuable. Use the New Page link to add a page or use the Edit Page link to make changes to an existing page.</p>\r\n    <p class=\"mt-btn-bar mt-btn-create-page\" if=\"!user.anonymous\">{{wiki.create{label:\"create a new page\", title:\"New page created by \"..user.name, button:false}}}</p>\r\n    <h4>Moving Pages</h4>\r\n    <p>Keeping your documentation in order has never been easier with MindTouch. Restructure your cont ent hiearchy to achieve optimal organization.</p>\r\n    <ol class=\"mt-small\">\r\n        <li>Go to the page you wish to move</li>\r\n        <li>Click <strong>Tools &gt; Move Page</strong></li>\r\n        <li>Use the <strong>Navigate</strong> box to find a new location</li>\r\n    </ol>\r\n    </div>\r\n    </li>\r\n    <li>\r\n    <div>\r\n    <h4>My User Space</h4>\r\n    <span if=\"!user.anonymous\">\r\n    <p>As a new user feel free to develop your user space which is located at:</p>\r\n    <p>{{web.link(user.uri,user.uri)}}</p>\r\n    <p class=\"mt-btn-bar mt-btn-user-page\"><a href=\"{{user.uri}}\">my user space</a></p>\r\n    </span> <span if=\"user.anonymous\">\r\n    <p>As a MindTouch user you will be able to develop your own user space which can be public or private.</p>\r\n    <p class=\"mt-btn-bar mt-btn-user-page\"><a title=\"Register\" href=\"/Special:UserRegistration\">register now</a></p>\r\n    </span>\r\n    <h4>Privacy and Permissions</h4>\r\n    <p>Need to keep something to yourself? Privacy with Mind Touch is easy and secure.</p>\r\n    <ol class=\"mt-small\">\r\n        <li>Go to the page you wish to protect</li>\r\n        <li>Click <strong>Tools &gt; Restrict Access</strong></li>\r\n        <li>Select the appropriate restriction level</li>\r\n    </ol>\r\n    <p style=\"text-align:center; margin:0\"><img alt=\"\" src=\"/skins/common/images/oobe/mt-img-privacy-settings.gif\" /></p>\r\n    </div>\r\n    </li>\r\n</ul>\r\n</div>\r\n<p style=\"margin:3px 0;text-align:right;padding-right:30px;\"><img alt=\"\" src=\"/skins/common/images/oobe/mt-img-privacy-legend.gif\" /></p>','',1,'20071103195811',0,0,0,0,0,'0','79928896804188',1,'','',0,0,'application/x.deki-text','',NULL,NULL,0,NULL),(34,10,'mt_user_tabs','<link rel=\"stylesheet\" type=\"text/css\" href=\"/skins/common/oobe.css\" />\r\n<div class=\"mt-tabs\">\r\n	<ul>\r\n		<li><a href=\"http://campaign.mindtouch.com/OOBE/Learn_More\">learn more</a></li>\r\n		<li><a href=\"#\" title=\"mt-document\">document</a></li>\r\n		<li><a href=\"#\" title=\"mt-develop\">develop</a></li>\r\n		<li class=\"title\">I WANT TO:</li>\r\n	</ul>\r\n</div>\r\n\r\n<div class=\"mt-content\">\r\n	<div class=\"mt-document hide\" >\r\n		{{mt_user_document()}}\r\n	</div>\r\n	\r\n	<div class=\"mt-develop\">\r\n		{{mt_user_develop()}}\r\n	</div>\r\n</div>\r\n\r\n<div>\r\n <script type=\"text/javascript\">\r\n	$(\"body\").ready( function() {\r\n		$(\".mt-tabs li:not(.selected) a\").click( function() {\r\nvar contenthref = $(this).attr(\"href\");\r\nif (contenthref==\'#\') {\r\nvar contentid = $(this).attr(\"title\");\r\n$(\".mt-tabs li a\").removeClass(\"selected\");\r\n$(this).addClass(\"selected\");\r\n\r\n$(\".mt-content > div:not(.hide)\").fadeOut( function() {\r\n	$(\".mt-content > div.\" + contentid).show();\r\n	\r\n	$(\".mt-content > div\").addClass(\"hide\");\r\n	$(\".mt-content > div.\" + contentid).removeClass(\"hide\");\r\n});\r\nreturn false;\r\n}\r\n\r\n		});\r\n		\r\n		$(\".mt-tabs li:not(.title):last a\").addClass(\"selected\");\r\n		\r\n		$(\".mt-tips\").each( function() {\r\n$(this).find(\"span:first\").addClass(\"selected\");	\r\n$(this).find(\"span:last\").attr(\"pos\",\"last\");	\r\n$(this).find(\"span.selected\").show();	\r\n		});\r\n		\r\n		setInterval ( \"nextTip()\", 6000 );\r\n	});\r\n	\r\n	function nextTip() {\r\n	\r\n	\r\n		$(\".mt-tips span.selected\").each( function() {\r\n$(this).hide();\r\n$ (this).removeClass(\"selected\");\r\n var pos = $(this).attr(\"pos\");\r\n\r\nif (pos==\"last\") {\r\n	$(this).parent().find(\"span:first\").addClass(\"selected\");\r\n	$(this).parent().find(\"span:first\").show();\r\n} else {\r\n	$(this).find(\"+ span\").addClass(\"selected\");\r\n	$(this).find(\"+ span\").show();\r\n}\r\n		});\r\n		\r\n	}\r\n</script>\r\n</div>','',1,'20071103195811',0,0,0,0,0,'0','79928896804188',1,'','',0,0,'application/x.deki-text','',NULL,NULL,0,NULL),(35,10,'mt_admin_tabs','<link rel=\"stylesheet\" type=\"text/css\" href=\"/skins/common/oobe.css\" />\r\n<div class=\"mt-tabs\">\r\n	<ul>\r\n		<li><a href=\"http://campaign.mindtouch.com/OOBE/Learn_More\">learn more</a></li>\r\n		<li><a href=\"#\" title=\"mt-kb\">a knowledge base</a></li>\r\n		<li><a href=\"#\" title=\"mt-extranet\">an extranet</a></li>\r\n		<li><a href=\"#\" title=\"mt-intranet\">an intranet</a></li>\r\n		<li class=\"title\">MY SITE WILL BE:</li>\r\n	</ul>\r\n</div>\r\n\r\n<div class=\"mt-content\">\r\n	<div class=\"mt-kb hide\" >\r\n		{{mt_admin_kb()}}\r\n	</div>\r\n	\r\n	<div class=\"mt-extranet hide\">\r\n		{{mt_admin_extranet();}}\r\n	</div>\r\n	\r\n	<div class=\"mt-intranet\">\r\n {{mt_admin_intranet();}}\r\n	</div>\r\n	\r\n	<div class=\"mt-enterprise-wiki hide\">\r\n		enterprise wiki\r\n	</div>\r\n</div>\r\n\r\n<div>\r\n<script type=\"text/javascript\">\r\n	$(\"body\").ready( function() {\r\n		$(\".mt-tabs li:not(.selected) a\").click( function() {\r\nvar contenthref = $(this).attr(\"href\");\r\nif (contenthref==\'#\') {\r\nvar contentid = $(this).attr(\"title\");\r\n$(\".mt-tabs li a\").removeClass(\"selected\");\r\n$(this).addClass(\"selected\");\r\n\r\n$(\".mt-content > div:not(.hide)\").fadeOut( function() {\r\n	$(\".mt-content > div.\" + contentid).fadeIn();\r\n	\r\n	$(\".mt-content > div\").addClass(\"hide\");\r\n	$(\".mt-content > div.\" + contentid).removeClass(\"hide\");\r\n});\r\nreturn false;\r\n}\r\n\r\n		});\r\n		\r\n		$(\".mt-tabs li:not(.title):last a\").addClass(\"selected\");\r\n		\r\n		$(\".mt-tips span:first\").addClass(\"selected\");	\r\n		$(\".mt-tips span:last\").attr(\"pos\",\"last\");	\r\n		\r\n		$(\".mt-tips span.selected\").fadeIn();	\r\n		\r\n		setInterval ( \"nextTip()\", 6000 );\r\n	});\r\n	\r\n function nextTip() {\r\n	\r\n	\r\n		$(\".mt-tips span.selected\").each( function() {\r\n$(this).hide();\r\n$(this).removeClass(\"selected\");\r\nvar pos = $(this).attr(\"pos\");\r\n\r\nif (pos==\"last\") {\r\n	$(this).parent().find(\"span:first\").addClass(\"selected\");\r\n	$(this).parent().find(\"span:first\").show();\r\n} else {\r\n	$(this).find(\"+ span\").addClass(\"selected\");\r\n	$(this).find(\"+ span\").show();\r\n}\r\n		});\r\n		\r\n	}\r\n</script>\r\n</div>\r\n','',1,'20071103195811',0,0,0,0,0,'0','79928896804188',1,'','',0,0,'application/x.deki-text','',NULL,NULL,0,NULL),(36,10,'mt_license','<a class=\"mt-tips\" href=\"http://campaign.mindtouch.com/OOBE/Contact\"> <span>Did you know MindTouch 2009 has database connectors?</span> <span>Did you know MindTouch 2009 has desktop tools?</span> <span>Did you know MindTouch 2009 has powerful mashup capabilities?</span> <span>Did you know MindTouch 2009 has premium  support and training?</span> <span>Did you know MindTouch 2009 has multi-tenant capabilities?</span> <span>Did you know MindTouch 2009 has rich dashboards?</span> </a> ','',1,'20071103195811',0,0,0,0,0,'0','79928896804188',1,'','',0,0,'application/x.deki-text','',NULL,NULL,0,NULL),(37,10,'mt_license_2009','<a class=\"mt-tips\" href=\"http://campaign.mindtouch.com/OOBE/Contact\"> <span>Did you know MindTouch 2009 has database connectors?</span> <span>Did you know MindTouch 2009 has desktop tools?</span> <span>Did you know MindTouch 2009 has powerful mashup capabilities?</span> <span>Did you know MindTouch 2009 has premium  support and training?</span> <span>Did you know MindTouch 2009 has multi-tenant capabilities?</span> <span>Did you know MindTouch 2009 has rich dashboards?</span> </a> ','',1,'20071103195811',0,0,0,0,0,'0','79928896804188',1,'','',0,0,'application/x.deki-text','',NULL,NULL,0,NULL),(38,2,'Admin','<p class=\"comment\">Welcome to your user page! You can customize your page by removing the content below.</p><p><span class=\"script\"> MindTouch_UserWelcome() </span></p>','page created, 16 words added',1,'20110711201618',1,0,0,1,0,'20110711201618','79889288798381',1,'','<p class=\"comment\">Welcome to your user page! You can customize your page by removing the content below.</p><p><span class=\"script\"> MindTouch_UserWelcome() </span></p>',0,0,'application/x.deki0805+xml','',NULL,NULL,0,NULL);
/*!40000 ALTER TABLE `pages` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `querycache`
--

DROP TABLE IF EXISTS `querycache`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `querycache` (
  `qc_type` char(32) NOT NULL default '',
  `qc_value` int(5) unsigned NOT NULL default '0',
  `qc_namespace` tinyint(2) unsigned NOT NULL default '0',
  `qc_title` char(255) NOT NULL default '',
  KEY `qc_type` (`qc_type`,`qc_value`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `querycache`
--

LOCK TABLES `querycache` WRITE;
/*!40000 ALTER TABLE `querycache` DISABLE KEYS */;
/*!40000 ALTER TABLE `querycache` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `recentchanges`
--

DROP TABLE IF EXISTS `recentchanges`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `recentchanges` (
  `rc_id` int(8) NOT NULL auto_increment,
  `rc_timestamp` varchar(14) NOT NULL default '',
  `rc_cur_time` varchar(14) NOT NULL default '',
  `rc_user` int(10) unsigned NOT NULL default '0',
  `rc_namespace` tinyint(3) unsigned NOT NULL default '0',
  `rc_title` varchar(255) NOT NULL default '',
  `rc_comment` varchar(255) NOT NULL default '',
  `rc_minor` tinyint(3) unsigned NOT NULL default '0',
  `rc_bot` tinyint(3) unsigned NOT NULL default '0',
  `rc_new` tinyint(3) unsigned NOT NULL default '0',
  `rc_cur_id` int(10) unsigned NOT NULL default '0',
  `rc_this_oldid` int(10) unsigned NOT NULL default '0',
  `rc_last_oldid` int(10) unsigned NOT NULL default '0',
  `rc_type` tinyint(3) unsigned NOT NULL default '0',
  `rc_moved_to_ns` tinyint(3) unsigned NOT NULL default '0',
  `rc_moved_to_title` varchar(255) NOT NULL default '',
  `rc_patrolled` tinyint(3) unsigned NOT NULL default '0',
  `rc_ip` varchar(15) NOT NULL default '',
  `rc_transaction_id` int(10) unsigned NOT NULL default '0',
  PRIMARY KEY  (`rc_id`),
  KEY `rc_timestamp` (`rc_timestamp`),
  KEY `rc_namespace_title` (`rc_namespace`,`rc_title`),
  KEY `rc_cur_id` (`rc_cur_id`),
  KEY `new_name_timestamp` (`rc_new`,`rc_namespace`,`rc_timestamp`),
  KEY `rc_ip` (`rc_ip`),
  KEY `rc_transaction_id` (`rc_transaction_id`),
  KEY `rc_user` (`rc_user`)
) ENGINE=MyISAM AUTO_INCREMENT=3 DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `recentchanges`
--

LOCK TABLES `recentchanges` WRITE;
/*!40000 ALTER TABLE `recentchanges` DISABLE KEYS */;
INSERT INTO `recentchanges` VALUES (1,'20110711195559','',1,0,'','page created',0,0,0,22,0,0,0,0,'',0,'',0),(2,'20110711201618','20110711201618',1,2,'Admin','page created, 16 words added',0,0,0,38,0,0,1,0,'',0,'',0);
/*!40000 ALTER TABLE `recentchanges` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `requestlog`
--

DROP TABLE IF EXISTS `requestlog`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `requestlog` (
  `rl_id` int(4) unsigned NOT NULL auto_increment,
  `rl_servicehost` varchar(64) NOT NULL,
  `rl_requesthost` varchar(64) NOT NULL,
  `rl_requesthostheader` varchar(64) NOT NULL,
  `rl_requestpath` varchar(512) NOT NULL,
  `rl_requestparams` varchar(512) default NULL,
  `rl_requestverb` varchar(8) NOT NULL,
  `rl_dekiuser` varchar(32) default NULL,
  `rl_origin` varchar(64) NOT NULL,
  `rl_servicefeature` varchar(128) NOT NULL,
  `rl_responsestatus` varchar(8) NOT NULL,
  `rl_executiontime` int(4) unsigned default NULL,
  `rl_response` varchar(2048) default NULL,
  `rl_timestamp` timestamp NOT NULL default CURRENT_TIMESTAMP,
  PRIMARY KEY  (`rl_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `requestlog`
--

LOCK TABLES `requestlog` WRITE;
/*!40000 ALTER TABLE `requestlog` DISABLE KEYS */;
/*!40000 ALTER TABLE `requestlog` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `requeststats`
--

DROP TABLE IF EXISTS `requeststats`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `requeststats` (
  `rs_id` int(4) unsigned NOT NULL auto_increment,
  `rs_numrequests` int(4) unsigned NOT NULL,
  `rs_servicehost` varchar(64) NOT NULL,
  `rs_requestverb` varchar(8) NOT NULL,
  `rs_servicefeature` varchar(128) NOT NULL,
  `rs_responsestatus` varchar(8) NOT NULL,
  `rs_exec_avg` int(4) unsigned NOT NULL,
  `rs_exec_std` int(4) unsigned NOT NULL,
  `rs_ts_start` timestamp NOT NULL default CURRENT_TIMESTAMP on update CURRENT_TIMESTAMP,
  `rs_ts_length` int(4) unsigned NOT NULL,
  PRIMARY KEY  (`rs_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `requeststats`
--

LOCK TABLES `requeststats` WRITE;
/*!40000 ALTER TABLE `requeststats` DISABLE KEYS */;
/*!40000 ALTER TABLE `requeststats` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `resourcecontents`
--

DROP TABLE IF EXISTS `resourcecontents`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `resourcecontents` (
  `rescontent_id` int(4) unsigned NOT NULL auto_increment,
  `rescontent_res_id` int(4) unsigned default NULL,
  `rescontent_res_rev` int(4) unsigned default NULL,
  `rescontent_value` mediumblob,
  `rescontent_mimetype` varchar(255) NOT NULL default '',
  `rescontent_size` int(4) unsigned NOT NULL default '0',
  `rescontent_location` varchar(255) default NULL,
  PRIMARY KEY  (`rescontent_id`),
  UNIQUE KEY `rescontent_res_id` (`rescontent_res_id`,`rescontent_res_rev`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `resourcecontents`
--

LOCK TABLES `resourcecontents` WRITE;
/*!40000 ALTER TABLE `resourcecontents` DISABLE KEYS */;
/*!40000 ALTER TABLE `resourcecontents` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `resourcefilemap`
--

DROP TABLE IF EXISTS `resourcefilemap`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `resourcefilemap` (
  `file_id` int(10) unsigned NOT NULL auto_increment,
  `resource_id` int(10) unsigned default NULL,
  PRIMARY KEY  (`file_id`),
  UNIQUE KEY `entity_id` (`resource_id`,`file_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `resourcefilemap`
--

LOCK TABLES `resourcefilemap` WRITE;
/*!40000 ALTER TABLE `resourcefilemap` DISABLE KEYS */;
/*!40000 ALTER TABLE `resourcefilemap` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `resourcerevs`
--

DROP TABLE IF EXISTS `resourcerevs`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `resourcerevs` (
  `resrev_id` int(4) unsigned NOT NULL auto_increment,
  `resrev_res_id` int(4) unsigned NOT NULL default '0',
  `resrev_rev` int(4) unsigned NOT NULL default '0',
  `resrev_user_id` int(4) unsigned NOT NULL default '0',
  `resrev_parent_id` int(4) unsigned default NULL,
  `resrev_parent_page_id` int(4) unsigned default NULL,
  `resrev_parent_user_id` int(4) unsigned default NULL,
  `resrev_change_mask` smallint(2) unsigned NOT NULL default '0',
  `resrev_name` varchar(255) NOT NULL default '',
  `resrev_change_description` varchar(255) default NULL,
  `resrev_timestamp` datetime NOT NULL default '0001-01-01 00:00:00',
  `resrev_content_id` int(4) unsigned NOT NULL default '0',
  `resrev_deleted` tinyint(1) unsigned NOT NULL default '0',
  `resrev_changeset_id` int(4) unsigned NOT NULL default '0',
  `resrev_size` int(4) unsigned NOT NULL default '0',
  `resrev_mimetype` varchar(255) NOT NULL default '',
  `resrev_language` varchar(255) default NULL,
  `resrev_is_hidden` tinyint(3) unsigned NOT NULL default '0',
  `resrev_meta` text,
  PRIMARY KEY  (`resrev_id`),
  UNIQUE KEY `resid_rev` (`resrev_res_id`,`resrev_rev`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `resourcerevs`
--

LOCK TABLES `resourcerevs` WRITE;
/*!40000 ALTER TABLE `resourcerevs` DISABLE KEYS */;
/*!40000 ALTER TABLE `resourcerevs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `resources`
--

DROP TABLE IF EXISTS `resources`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `resources` (
  `res_id` int(4) unsigned NOT NULL auto_increment,
  `res_headrev` int(4) unsigned NOT NULL default '0',
  `res_type` tinyint(1) unsigned NOT NULL default '0',
  `res_deleted` tinyint(1) unsigned NOT NULL default '0',
  `res_create_timestamp` datetime NOT NULL default '0001-01-01 00:00:00',
  `res_update_timestamp` datetime NOT NULL default '0001-01-01 00:00:00',
  `res_create_user_id` int(4) unsigned NOT NULL default '0',
  `res_update_user_id` int(4) unsigned NOT NULL default '0',
  `resrev_rev` int(4) unsigned NOT NULL default '0',
  `resrev_user_id` int(4) unsigned NOT NULL default '0',
  `resrev_parent_id` int(4) unsigned default NULL,
  `resrev_parent_page_id` int(4) unsigned default NULL,
  `resrev_parent_user_id` int(4) unsigned default NULL,
  `resrev_change_mask` smallint(2) unsigned NOT NULL default '0',
  `resrev_name` varchar(255) NOT NULL default '',
  `resrev_change_description` varchar(255) default NULL,
  `resrev_timestamp` datetime NOT NULL default '0001-01-01 00:00:00',
  `resrev_content_id` int(4) unsigned NOT NULL default '0',
  `resrev_deleted` tinyint(1) unsigned NOT NULL default '0',
  `resrev_changeset_id` int(4) unsigned NOT NULL default '0',
  `resrev_size` int(4) unsigned NOT NULL default '0',
  `resrev_mimetype` varchar(255) NOT NULL default '',
  `resrev_language` varchar(255) default NULL,
  `resrev_is_hidden` tinyint(3) unsigned NOT NULL default '0',
  `resrev_meta` text,
  PRIMARY KEY  (`res_id`),
  KEY `changeset` (`resrev_changeset_id`),
  KEY `parent_resource` (`resrev_parent_id`),
  KEY `parent_page` (`resrev_parent_page_id`),
  KEY `parent_user` (`resrev_parent_user_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `resources`
--

LOCK TABLES `resources` WRITE;
/*!40000 ALTER TABLE `resources` DISABLE KEYS */;
/*!40000 ALTER TABLE `resources` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `restrictions`
--

DROP TABLE IF EXISTS `restrictions`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `restrictions` (
  `restriction_id` int(4) unsigned NOT NULL auto_increment,
  `restriction_name` varchar(255) NOT NULL,
  `restriction_perm_flags` mediumint(8) unsigned NOT NULL,
  `restriction_creator_user_id` int(10) unsigned NOT NULL,
  `restriction_last_edit` timestamp NOT NULL default CURRENT_TIMESTAMP on update CURRENT_TIMESTAMP,
  PRIMARY KEY  (`restriction_id`)
) ENGINE=MyISAM AUTO_INCREMENT=4 DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `restrictions`
--

LOCK TABLES `restrictions` WRITE;
/*!40000 ALTER TABLE `restrictions` DISABLE KEYS */;
INSERT INTO `restrictions` VALUES (1,'Public',6143,1,'2011-07-11 19:55:59'),(2,'Semi-Public',15,1,'2011-07-11 19:55:59'),(3,'Private',1,1,'2011-07-11 19:55:59');
/*!40000 ALTER TABLE `restrictions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `roles`
--

DROP TABLE IF EXISTS `roles`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `roles` (
  `role_id` int(4) unsigned NOT NULL auto_increment,
  `role_name` varchar(255) NOT NULL,
  `role_perm_flags` bigint(8) unsigned NOT NULL,
  `role_creator_user_id` int(10) unsigned NOT NULL,
  `role_last_edit` timestamp NOT NULL default CURRENT_TIMESTAMP on update CURRENT_TIMESTAMP,
  PRIMARY KEY  (`role_id`)
) ENGINE=MyISAM AUTO_INCREMENT=6 DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `roles`
--

LOCK TABLES `roles` WRITE;
/*!40000 ALTER TABLE `roles` DISABLE KEYS */;
INSERT INTO `roles` VALUES (1,'None',0,1,'2011-07-11 19:55:59'),(2,'Guest',1,1,'2011-07-11 19:55:59'),(3,'Viewer',15,1,'2011-07-11 19:55:59'),(4,'Contributor',1343,1,'2011-07-11 19:55:59'),(5,'Admin',9223372036854779903,1,'2011-07-11 19:55:59');
/*!40000 ALTER TABLE `roles` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `service_config`
--

DROP TABLE IF EXISTS `service_config`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `service_config` (
  `config_id` int(10) unsigned NOT NULL auto_increment,
  `service_id` int(4) unsigned NOT NULL,
  `config_name` char(255) NOT NULL,
  `config_value` text,
  PRIMARY KEY  (`config_id`)
) ENGINE=MyISAM AUTO_INCREMENT=64 DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

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
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `service_prefs` (
  `pref_id` int(10) unsigned NOT NULL auto_increment,
  `service_id` int(4) unsigned NOT NULL,
  `pref_name` char(255) NOT NULL,
  `pref_value` text,
  PRIMARY KEY  (`pref_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

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
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
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
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `services`
--

LOCK TABLES `services` WRITE;
/*!40000 ALTER TABLE `services` DISABLE KEYS */;
INSERT INTO `services` VALUES (1,'AUTH','http://services.mindtouch.com/deki/draft/2006/11/dekiwiki','local://4b8285ae06f9bb86a355b4d00ab31f92/deki','Local',1,1,'','2011-07-11 19:55:59'),(2,'EXT','sid://mindtouch.com/2007/12/dekiscript',NULL,'AccuWeather',1,1,'System.Exception: unable to initialize service (async operation timed out)\n  at MindTouch.Dream.DreamService+<CreateService_Helper>d__19.MoveNext () [0x00000] in <filename unknown>:0 \n  at MindTouch.Tasking.Coroutine.Continue () [0x00000] in <filename unknown>:0 \n   --- End of exception stack trace ---\n   at MindTouch.Dream.DreamService.CreateService_Helper(String path, String sid, XDoc config, Result`1 result)\n   --- End of coroutine stack trace ---','2011-07-11 19:55:59'),(3,'ext','sid://mindtouch.com/2007/12/dekiscript',NULL,'AddThis',1,0,NULL,'2011-07-11 19:55:59'),(4,'EXT','sid://mindtouch.com/2007/12/dapper','local://4b8285ae06f9bb86a355b4d00ab31f92/deki/services/default/4','Dapper',1,1,'','2011-07-11 19:55:59'),(6,'EXT','sid://mindtouch.com/2007/12/dekiscript',NULL,'Digg',1,1,'System.Exception: unable to initialize service (async operation timed out)\n  at MindTouch.Dream.DreamService+<CreateService_Helper>d__19.MoveNext () [0x00000] in <filename unknown>:0 \n  at MindTouch.Tasking.Coroutine.Continue () [0x00000] in <filename unknown>:0 \n   --- End of exception stack trace ---\n   at MindTouch.Dream.DreamService.CreateService_Helper(String path, String sid, XDoc config, Result`1 result)\n   --- End of coroutine stack trace ---','2011-07-11 19:55:59'),(8,'EXT','sid://mindtouch.com/2007/12/dekiscript',NULL,'Flickr',1,1,'System.Exception: unable to initialize service (async operation timed out)\n  at MindTouch.Dream.DreamService+<CreateService_Helper>d__19.MoveNext () [0x00000] in <filename unknown>:0 \n  at MindTouch.Tasking.Coroutine.Continue () [0x00000] in <filename unknown>:0 \n   --- End of exception stack trace ---\n   at MindTouch.Dream.DreamService.CreateService_Helper(String path, String sid, XDoc config, Result`1 result)\n   --- End of coroutine stack trace ---','2011-07-11 19:55:59'),(9,'EXT','sid://mindtouch.com/2007/12/dekiscript',NULL,'FlowPlayer',1,1,'System.Exception: unable to initialize service (async operation timed out)\n  at MindTouch.Dream.DreamService+<CreateService_Helper>d__19.MoveNext () [0x00000] in <filename unknown>:0 \n  at MindTouch.Tasking.Coroutine.Continue () [0x00000] in <filename unknown>:0 \n   --- End of exception stack trace ---\n   at MindTouch.Dream.DreamService.CreateService_Helper(String path, String sid, XDoc config, Result`1 result)\n   --- End of coroutine stack trace ---','2011-07-11 19:55:59'),(10,'ext','sid://mindtouch.com/2007/06/google',NULL,'Google',1,0,NULL,'2011-07-11 19:55:59'),(11,'ext','sid://mindtouch.com/2007/06/graphviz',NULL,'Graphviz',1,0,NULL,'2011-07-11 19:55:59'),(12,'EXT','sid://mindtouch.com/2007/12/dekiscript',NULL,'Gravatar',1,1,'System.Exception: unable to initialize service (async operation timed out)\n  at MindTouch.Dream.DreamService+<CreateService_Helper>d__19.MoveNext () [0x00000] in <filename unknown>:0 \n  at MindTouch.Tasking.Coroutine.Continue () [0x00000] in <filename unknown>:0 \n   --- End of exception stack trace ---\n   at MindTouch.Dream.DreamService.CreateService_Helper(String path, String sid, XDoc config, Result`1 result)\n   --- End of coroutine stack trace ---','2011-07-11 19:55:59'),(13,'ext','sid://mindtouch.com/2007/06/imagemagick',NULL,'ImageMagick',1,0,NULL,'2011-07-11 19:55:59'),(14,'ext','sid://mindtouch.com/2008/02/jira',NULL,'Jira',1,0,NULL,'2011-07-11 19:55:59'),(15,'EXT','sid://mindtouch.com/2007/12/dekiscript',NULL,'LinkedIn',1,1,'System.Exception: unable to initialize service (async operation timed out)\n  at MindTouch.Dream.DreamService+<CreateService_Helper>d__19.MoveNext () [0x00000] in <filename unknown>:0 \n  at MindTouch.Tasking.Coroutine.Continue () [0x00000] in <filename unknown>:0 \n   --- End of exception stack trace ---\n   at MindTouch.Dream.DreamService.CreateService_Helper(String path, String sid, XDoc config, Result`1 result)\n   --- End of coroutine stack trace ---','2011-07-11 19:55:59'),(16,'ext','sid://mindtouch.com/2008/01/mantis',NULL,'Mantis',1,0,NULL,'2011-07-11 19:55:59'),(17,'ext','sid://mindtouch.com/2007/06/math',NULL,'Math',1,0,NULL,'2011-07-11 19:55:59'),(18,'EXT','sid://mindtouch.com/2007/06/media','local://4b8285ae06f9bb86a355b4d00ab31f92/deki/services/default/18','Multimedia',1,1,'','2011-07-11 19:55:59'),(19,'ext','sid://mindtouch.com/2007/06/mysql',NULL,'MySql',1,0,NULL,'2011-07-11 19:55:59'),(7,'EXT','sid://mindtouch.com/2007/06/feed','local://4b8285ae06f9bb86a355b4d00ab31f92/deki/services/default/7','Atom/RSS Feeds',1,1,'','2011-07-11 19:55:59'),(21,'ext','sid://mindtouch.com/2007/12/dekiscript',NULL,'PayPal',1,0,NULL,'2011-07-11 19:55:59'),(22,'EXT','sid://mindtouch.com/2007/12/dekiscript',NULL,'Scratch',1,1,'System.Exception: unable to initialize service (async operation timed out)\n  at MindTouch.Dream.DreamService+<CreateService_Helper>d__19.MoveNext () [0x00000] in <filename unknown>:0 \n  at MindTouch.Tasking.Coroutine.Continue () [0x00000] in <filename unknown>:0 \n   --- End of exception stack trace ---\n   at MindTouch.Dream.DreamService.CreateService_Helper(String path, String sid, XDoc config, Result`1 result)\n   --- End of coroutine stack trace ---','2011-07-11 19:55:59'),(23,'ext','sid://mindtouch.com/2007/12/dekiscript',NULL,'Scribd',1,0,NULL,'2011-07-11 19:55:59'),(24,'EXT','sid://mindtouch.com/2008/02/silverlight','local://4b8285ae06f9bb86a355b4d00ab31f92/deki/services/default/24','Silverlight',1,1,'','2011-07-11 19:55:59'),(25,'EXT','sid://mindtouch.com/2007/12/dekiscript',NULL,'Skype',1,1,'System.Exception: unable to initialize service (async operation timed out)\n  at MindTouch.Dream.DreamService+<CreateService_Helper>d__19.MoveNext () [0x00000] in <filename unknown>:0 \n  at MindTouch.Tasking.Coroutine.Continue () [0x00000] in <filename unknown>:0 \n   --- End of exception stack trace ---\n   at MindTouch.Dream.DreamService.CreateService_Helper(String path, String sid, XDoc config, Result`1 result)\n   --- End of coroutine stack trace ---','2011-07-11 19:55:59'),(26,'EXT','sid://mindtouch.com/2007/12/dekiscript',NULL,'Spoiler',1,1,'System.Exception: unable to initialize service (async operation timed out)\n  at MindTouch.Dream.DreamService+<CreateService_Helper>d__19.MoveNext () [0x00000] in <filename unknown>:0 \n  at MindTouch.Tasking.Coroutine.Continue () [0x00000] in <filename unknown>:0 \n   --- End of exception stack trace ---\n   at MindTouch.Dream.DreamService.CreateService_Helper(String path, String sid, XDoc config, Result`1 result)\n   --- End of coroutine stack trace ---','2011-07-11 19:55:59'),(27,'ext','sid://mindtouch.com/2008/02/svn',NULL,'Subversion',1,0,NULL,'2011-07-11 19:55:59'),(28,'EXT','sid://mindtouch.com/2008/05/svg','local://4b8285ae06f9bb86a355b4d00ab31f92/deki/services/default/28','SVG',1,1,'','2011-07-11 19:55:59'),(29,'EXT','sid://mindtouch.com/2007/12/dekiscript',NULL,'Syntax Highlighter',1,1,'System.Exception: unable to initialize service (async operation timed out)\n  at MindTouch.Dream.DreamService+<CreateService_Helper>d__19.MoveNext () [0x00000] in <filename unknown>:0 \n  at MindTouch.Tasking.Coroutine.Continue () [0x00000] in <filename unknown>:0 \n   --- End of exception stack trace ---\n   at MindTouch.Dream.DreamService.CreateService_Helper(String path, String sid, XDoc config, Result`1 result)\n   --- End of coroutine stack trace ---','2011-07-11 19:55:59'),(30,'ext','sid://mindtouch.com/2008/02/trac',NULL,'Trac',1,0,NULL,'2011-07-11 19:55:59'),(31,'EXT','sid://mindtouch.com/2007/12/dekiscript',NULL,'Twitter',1,1,'System.Exception: unable to initialize service (async operation timed out)\n  at MindTouch.Dream.DreamService+<CreateService_Helper>d__19.MoveNext () [0x00000] in <filename unknown>:0 \n  at MindTouch.Tasking.Coroutine.Continue () [0x00000] in <filename unknown>:0 \n   --- End of exception stack trace ---\n   at MindTouch.Dream.DreamService.CreateService_Helper(String path, String sid, XDoc config, Result`1 result)\n   --- End of coroutine stack trace ---','2011-07-11 19:55:59'),(32,'EXT','sid://mindtouch.com/2007/12/dekiscript',NULL,'WidgetBox',1,1,'System.Exception: unable to initialize service (async operation timed out)\n  at MindTouch.Dream.DreamService+<CreateService_Helper>d__19.MoveNext () [0x00000] in <filename unknown>:0 \n  at MindTouch.Tasking.Coroutine.Continue () [0x00000] in <filename unknown>:0 \n   --- End of exception stack trace ---\n   at MindTouch.Dream.DreamService.CreateService_Helper(String path, String sid, XDoc config, Result`1 result)\n   --- End of coroutine stack trace ---','2011-07-11 19:55:59'),(33,'EXT','sid://mindtouch.com/2007/07/windows.live','local://4b8285ae06f9bb86a355b4d00ab31f92/deki/services/default/33','Windows Live',1,1,'','2011-07-11 19:55:59'),(35,'EXT','sid://mindtouch.com/2007/12/dekiscript',NULL,'YUI Media Player',1,1,'System.Exception: unable to initialize service (async operation timed out)\n  at MindTouch.Dream.DreamService+<CreateService_Helper>d__19.MoveNext () [0x00000] in <filename unknown>:0 \n  at MindTouch.Tasking.Coroutine.Continue () [0x00000] in <filename unknown>:0 \n   --- End of exception stack trace ---\n   at MindTouch.Dream.DreamService.CreateService_Helper(String path, String sid, XDoc config, Result`1 result)\n   --- End of coroutine stack trace ---','2011-07-11 19:55:59'),(37,'EXT','sid://mindtouch.com/2007/12/dekiscript',NULL,'Lightbox',1,1,'System.Exception: unable to initialize service (async operation timed out)\n  at MindTouch.Dream.DreamService+<CreateService_Helper>d__19.MoveNext () [0x00000] in <filename unknown>:0 \n  at MindTouch.Tasking.Coroutine.Continue () [0x00000] in <filename unknown>:0 \n   --- End of exception stack trace ---\n   at MindTouch.Dream.DreamService.CreateService_Helper(String path, String sid, XDoc config, Result`1 result)\n   --- End of coroutine stack trace ---','2011-07-11 19:55:59'),(38,'EXT','sid://mindtouch.com/2007/12/dekiscript',NULL,'Quicktime',1,1,'System.Exception: unable to initialize service (async operation timed out)\n  at MindTouch.Dream.DreamService+<CreateService_Helper>d__19.MoveNext () [0x00000] in <filename unknown>:0 \n  at MindTouch.Tasking.Coroutine.Continue () [0x00000] in <filename unknown>:0 \n   --- End of exception stack trace ---\n   at MindTouch.Dream.DreamService.CreateService_Helper(String path, String sid, XDoc config, Result`1 result)\n   --- End of coroutine stack trace ---','2011-07-11 19:55:59'),(39,'EXT','sid://mindtouch.com/2007/12/dekiscript',NULL,'Remember The Milk',1,1,'System.Exception: unable to initialize service (async operation timed out)\n  at MindTouch.Dream.DreamService+<CreateService_Helper>d__19.MoveNext () [0x00000] in <filename unknown>:0 \n  at MindTouch.Tasking.Coroutine.Continue () [0x00000] in <filename unknown>:0 \n   --- End of exception stack trace ---\n   at MindTouch.Dream.DreamService.CreateService_Helper(String path, String sid, XDoc config, Result`1 result)\n   --- End of coroutine stack trace ---','2011-07-11 19:55:59'),(40,'EXT','sid://mindtouch.com/2007/12/dekiscript',NULL,'Zoho',1,1,'System.Exception: unable to initialize service (async operation timed out)\n  at MindTouch.Dream.DreamService+<CreateService_Helper>d__19.MoveNext () [0x00000] in <filename unknown>:0 \n  at MindTouch.Tasking.Coroutine.Continue () [0x00000] in <filename unknown>:0 \n   --- End of exception stack trace ---\n   at MindTouch.Dream.DreamService.CreateService_Helper(String path, String sid, XDoc config, Result`1 result)\n   --- End of coroutine stack trace ---','2011-07-11 19:55:59'),(41,'ext','sid://mindtouch.com/ent/2008/05/salesforce',NULL,'Salesforce',1,0,NULL,'2011-07-11 19:55:59'),(42,'ext','sid://mindtouch.com/ent/2008/05/sugarcrm',NULL,'SugarCRM',1,0,NULL,'2011-07-11 19:55:59'),(43,'ext','sid://mindtouch.com/ext/2009/12/anychart',NULL,'AnyChart',1,0,NULL,'2011-07-11 19:55:59'),(44,'ext','sid://mindtouch.com/ext/2009/12/anygantt',NULL,'AnyGantt',1,0,NULL,'2011-07-11 19:55:59'),(20,'EXT','sid://mindtouch.com/2007/12/dekiscript',NULL,'PageBus',1,1,'System.Exception: unable to initialize service (async operation timed out)\n  at MindTouch.Dream.DreamService+<CreateService_Helper>d__19.MoveNext () [0x00000] in <filename unknown>:0 \n  at MindTouch.Tasking.Coroutine.Continue () [0x00000] in <filename unknown>:0 \n   --- End of exception stack trace ---\n   at MindTouch.Dream.DreamService.CreateService_Helper(String path, String sid, XDoc config, Result`1 result)\n   --- End of coroutine stack trace ---','2011-07-11 19:55:59'),(5,'EXT','sid://mindtouch.com/2007/12/dekiscript',NULL,'DHtml',1,1,'System.Exception: unable to initialize service (async operation timed out)\n  at MindTouch.Dream.DreamService+<CreateService_Helper>d__19.MoveNext () [0x00000] in <filename unknown>:0 \n  at MindTouch.Tasking.Coroutine.Continue () [0x00000] in <filename unknown>:0 \n   --- End of exception stack trace ---\n   at MindTouch.Dream.DreamService.CreateService_Helper(String path, String sid, XDoc config, Result`1 result)\n   --- End of coroutine stack trace ---','2011-07-11 19:55:59'),(34,'EXT','sid://mindtouch.com/2007/06/yahoo','local://4b8285ae06f9bb86a355b4d00ab31f92/deki/services/default/34','Yahoo!',1,1,'','2011-07-11 19:55:59'),(36,'EXT','sid://mindtouch.com/2007/12/dekiscript',NULL,'EditGrid',1,1,'System.Exception: unable to initialize service (async operation timed out)\n  at MindTouch.Dream.DreamService+<CreateService_Helper>d__19.MoveNext () [0x00000] in <filename unknown>:0 \n  at MindTouch.Tasking.Coroutine.Continue () [0x00000] in <filename unknown>:0 \n   --- End of exception stack trace ---\n   at MindTouch.Dream.DreamService.CreateService_Helper(String path, String sid, XDoc config, Result`1 result)\n   --- End of coroutine stack trace ---','2011-07-11 19:55:59');
/*!40000 ALTER TABLE `services` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tag_map`
--

DROP TABLE IF EXISTS `tag_map`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `tag_map` (
  `tagmap_id` int(10) unsigned NOT NULL auto_increment,
  `tagmap_page_id` int(10) unsigned NOT NULL,
  `tagmap_tag_id` int(4) unsigned NOT NULL,
  PRIMARY KEY  (`tagmap_id`),
  UNIQUE KEY `tagmap_page_id` (`tagmap_page_id`,`tagmap_tag_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `tag_map`
--

LOCK TABLES `tag_map` WRITE;
/*!40000 ALTER TABLE `tag_map` DISABLE KEYS */;
/*!40000 ALTER TABLE `tag_map` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tags`
--

DROP TABLE IF EXISTS `tags`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `tags` (
  `tag_id` int(4) unsigned NOT NULL auto_increment,
  `tag_name` varchar(255) NOT NULL default '',
  `tag_type` tinyint(2) unsigned NOT NULL default '0',
  PRIMARY KEY  (`tag_id`),
  UNIQUE KEY `tag_name` (`tag_name`,`tag_type`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `tags`
--

LOCK TABLES `tags` WRITE;
/*!40000 ALTER TABLE `tags` DISABLE KEYS */;
/*!40000 ALTER TABLE `tags` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `transactions`
--

DROP TABLE IF EXISTS `transactions`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `transactions` (
  `t_id` int(4) NOT NULL auto_increment,
  `t_timestamp` datetime NOT NULL,
  `t_user_id` int(4) NOT NULL,
  `t_page_id` int(4) unsigned default NULL,
  `t_title` varchar(255) default NULL,
  `t_namespace` tinyint(2) unsigned default NULL,
  `t_type` tinyint(2) default NULL,
  `t_reverted` tinyint(1) NOT NULL default '0',
  `t_revert_user_id` int(4) unsigned default NULL,
  `t_revert_timestamp` datetime default NULL,
  `t_revert_reason` varchar(255) default NULL,
  PRIMARY KEY  (`t_id`),
  KEY `t_timestamp` (`t_timestamp`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `transactions`
--

LOCK TABLES `transactions` WRITE;
/*!40000 ALTER TABLE `transactions` DISABLE KEYS */;
/*!40000 ALTER TABLE `transactions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_grants`
--

DROP TABLE IF EXISTS `user_grants`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `user_grants` (
  `user_grant_id` int(10) unsigned NOT NULL auto_increment,
  `page_id` int(10) unsigned NOT NULL,
  `user_id` int(10) unsigned NOT NULL,
  `role_id` int(4) unsigned NOT NULL,
  `creator_user_id` int(10) unsigned NOT NULL,
  `expire_date` datetime default NULL,
  `last_edit` timestamp NOT NULL default CURRENT_TIMESTAMP on update CURRENT_TIMESTAMP,
  PRIMARY KEY  (`user_grant_id`),
  UNIQUE KEY `page_id` (`page_id`,`user_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `user_grants`
--

LOCK TABLES `user_grants` WRITE;
/*!40000 ALTER TABLE `user_grants` DISABLE KEYS */;
/*!40000 ALTER TABLE `user_grants` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_groups`
--

DROP TABLE IF EXISTS `user_groups`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `user_groups` (
  `user_id` int(10) NOT NULL,
  `group_id` int(10) NOT NULL,
  `last_edit` timestamp NOT NULL default CURRENT_TIMESTAMP on update CURRENT_TIMESTAMP,
  UNIQUE KEY `user_id` (`user_id`,`group_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `user_groups`
--

LOCK TABLES `user_groups` WRITE;
/*!40000 ALTER TABLE `user_groups` DISABLE KEYS */;
/*!40000 ALTER TABLE `user_groups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `users` (
  `user_id` int(10) unsigned NOT NULL auto_increment,
  `user_name` varchar(255) NOT NULL,
  `user_real_name` varchar(255) default NULL,
  `user_password` tinyblob NOT NULL,
  `user_newpassword` tinyblob NOT NULL,
  `user_email` varchar(255) default NULL,
  `user_touched` varchar(14) NOT NULL default '',
  `user_token` varchar(32) NOT NULL default '',
  `user_role_id` int(4) unsigned NOT NULL,
  `user_active` tinyint(1) unsigned NOT NULL,
  `user_external_name` varchar(255) default NULL,
  `user_service_id` int(4) unsigned NOT NULL,
  `user_builtin` tinyint(1) unsigned NOT NULL default '0',
  `user_create_timestamp` datetime NOT NULL default '0001-01-01 00:00:00',
  `user_language` varchar(255) default NULL,
  `user_timezone` varchar(255) default NULL,
  PRIMARY KEY  (`user_id`),
  UNIQUE KEY `user_name` (`user_name`,`user_service_id`),
  UNIQUE KEY `user_real_name_service_id` (`user_external_name`,`user_service_id`)
) ENGINE=MyISAM AUTO_INCREMENT=3 DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (1,'Admin','','77da245e656a56818e6d7d874e1dd5c7','','lorchard@mozilla.com','20110711201719','2158a249b6b8368a738bf81d97627be1',5,1,NULL,1,1,'0001-01-01 00:00:00',NULL,NULL),(2,'Anonymous','Anonymous User','','','','20110711201733','',3,1,NULL,1,1,'0001-01-01 00:00:00',NULL,NULL);
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `watchlist`
--

DROP TABLE IF EXISTS `watchlist`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `watchlist` (
  `wl_user` int(5) unsigned NOT NULL default '0',
  `wl_namespace` tinyint(2) unsigned NOT NULL default '0',
  `wl_title` varchar(255) NOT NULL default '',
  UNIQUE KEY `wl_user` (`wl_user`,`wl_namespace`,`wl_title`),
  KEY `namespace_title` (`wl_namespace`,`wl_title`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `watchlist`
--

LOCK TABLES `watchlist` WRITE;
/*!40000 ALTER TABLE `watchlist` DISABLE KEYS */;
/*!40000 ALTER TABLE `watchlist` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2011-07-11 22:05:43
