-- MySQL dump 10.13  Distrib 5.1.54, for apple-darwin10.6.0 (i386)
--
-- Host: localhost    Database: kuma
-- ------------------------------------------------------
-- Server version	5.1.54-log

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
-- Table structure for table `actioncounters_actioncounterunique`
--

DROP TABLE IF EXISTS `actioncounters_actioncounterunique`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `actioncounters_actioncounterunique` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `content_type_id` int(11) NOT NULL,
  `object_pk` varchar(32) NOT NULL,
  `name` varchar(64) NOT NULL,
  `total` int(11) DEFAULT '0',
  `ip` varchar(40) DEFAULT NULL,
  `session_key` varchar(40) DEFAULT NULL,
  `user_agent` varchar(255) DEFAULT NULL,
  `user_id` int(11) DEFAULT NULL,
  `modified` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `actioncounters_actioncounterunique_e4470c6e` (`content_type_id`),
  KEY `actioncounters_actioncounterunique_52094d6e` (`name`),
  KEY `actioncounters_actioncounterunique_49a8a8f2` (`ip`),
  KEY `actioncounters_actioncounterunique_4cac0564` (`session_key`),
  KEY `actioncounters_actioncounterunique_c8b0e61e` (`user_agent`),
  KEY `actioncounters_actioncounterunique_fbfc09f1` (`user_id`),
  CONSTRAINT `content_type_id_refs_id_a1fb3291` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `user_id_refs_id_b752f625` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `actioncounters_testmodel`
--

DROP TABLE IF EXISTS `actioncounters_testmodel`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `actioncounters_testmodel` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `title` varchar(255) NOT NULL,
  `views_total` int(11) NOT NULL,
  `views_recent` int(11) NOT NULL,
  `boogs_total` int(11) NOT NULL,
  `boogs_recent` int(11) NOT NULL,
  `likes_total` int(11) NOT NULL,
  `likes_recent` int(11) NOT NULL,
  `frobs_total` int(11) NOT NULL,
  `frobs_recent` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `title` (`title`),
  KEY `actioncounters_testmodel_634da739` (`views_total`),
  KEY `actioncounters_testmodel_e23cedef` (`views_recent`),
  KEY `actioncounters_testmodel_77bf8c79` (`boogs_total`),
  KEY `actioncounters_testmodel_51430bd1` (`boogs_recent`),
  KEY `actioncounters_testmodel_2078387` (`likes_total`),
  KEY `actioncounters_testmodel_6ba6244d` (`likes_recent`),
  KEY `actioncounters_testmodel_5ded18b5` (`frobs_total`),
  KEY `actioncounters_testmodel_59ecea45` (`frobs_recent`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `auth_group`
--

DROP TABLE IF EXISTS `auth_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_group` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(80) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `auth_group_permissions`
--

DROP TABLE IF EXISTS `auth_group_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_group_permissions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `group_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `group_id` (`group_id`,`permission_id`),
  KEY `permission_id_refs_id_5886d21f` (`permission_id`),
  CONSTRAINT `group_id_refs_id_3cea63fe` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `permission_id_refs_id_5886d21f` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `auth_message`
--

DROP TABLE IF EXISTS `auth_message`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_message` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `message` longtext NOT NULL,
  PRIMARY KEY (`id`),
  KEY `auth_message_user_id_idx` (`user_id`),
  CONSTRAINT `user_id_refs_id_650f49a6` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `auth_permission`
--

DROP TABLE IF EXISTS `auth_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_permission` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `content_type_id` int(11) NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `content_type_id` (`content_type_id`,`codename`),
  KEY `auth_permission_content_type_id_idx` (`content_type_id`)
) ENGINE=InnoDB AUTO_INCREMENT=112 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `auth_user`
--

DROP TABLE IF EXISTS `auth_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_user` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(30) NOT NULL,
  `first_name` varchar(30) NOT NULL,
  `last_name` varchar(30) NOT NULL,
  `email` varchar(75) NOT NULL,
  `password` varchar(128) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `last_login` datetime NOT NULL,
  `date_joined` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `auth_user_groups`
--

DROP TABLE IF EXISTS `auth_user_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_user_groups` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `group_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`,`group_id`),
  KEY `group_id_refs_id_f116770` (`group_id`),
  CONSTRAINT `group_id_refs_id_f116770` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `user_id_refs_id_7ceef80f` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `auth_user_user_permissions`
--

DROP TABLE IF EXISTS `auth_user_user_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_user_user_permissions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`,`permission_id`),
  KEY `permission_id_refs_id_67e79cb` (`permission_id`),
  CONSTRAINT `permission_id_refs_id_67e79cb` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `user_id_refs_id_dfbab7d` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `contentflagging_contentflag`
--

DROP TABLE IF EXISTS `contentflagging_contentflag`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `contentflagging_contentflag` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `flag_status` varchar(16) NOT NULL,
  `flag_type` varchar(64) NOT NULL,
  `explanation` longtext NOT NULL,
  `content_type_id` int(11) NOT NULL,
  `object_pk` varchar(32) NOT NULL,
  `ip` varchar(40) DEFAULT NULL,
  `session_key` varchar(40) DEFAULT NULL,
  `user_agent` varchar(255) DEFAULT NULL,
  `user_id` int(11) DEFAULT NULL,
  `created` datetime NOT NULL,
  `modified` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `contentflagging_contentflag_68c2f437` (`flag_type`),
  KEY `contentflagging_contentflag_e4470c6e` (`content_type_id`),
  KEY `contentflagging_contentflag_fbfc09f1` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `demos_submission`
--

DROP TABLE IF EXISTS `demos_submission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `demos_submission` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `title` varchar(255) NOT NULL,
  `slug` varchar(50) NOT NULL,
  `summary` varchar(255) NOT NULL,
  `description` longtext NOT NULL,
  `featured` tinyint(1) NOT NULL,
  `hidden` tinyint(1) NOT NULL,
  `tags` varchar(255) NOT NULL,
  `screenshot_1` varchar(100) NOT NULL,
  `screenshot_2` varchar(100) NOT NULL,
  `screenshot_3` varchar(100) NOT NULL,
  `screenshot_4` varchar(100) NOT NULL,
  `screenshot_5` varchar(100) NOT NULL,
  `video_url` varchar(200) DEFAULT NULL,
  `demo_package` varchar(100) NOT NULL,
  `source_code_url` varchar(200) DEFAULT NULL,
  `license_name` varchar(64) NOT NULL,
  `creator_id` int(11) DEFAULT NULL,
  `created` datetime NOT NULL,
  `modified` datetime NOT NULL,
  `likes_total` int(11) NOT NULL,
  `likes_recent` int(11) NOT NULL,
  `launches_total` int(11) NOT NULL,
  `launches_recent` int(11) NOT NULL,
  `comments_total` int(11) NOT NULL DEFAULT '0',
  `navbar_optout` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `title` (`title`),
  UNIQUE KEY `slug` (`slug`),
  KEY `demos_submission_f97a5119` (`creator_id`),
  KEY `demos_submission_2078387` (`likes_total`),
  KEY `demos_submission_6ba6244d` (`likes_recent`),
  KEY `demos_submission_1dc8f9` (`launches_total`),
  KEY `demos_submission_3984f161` (`launches_recent`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `django_admin_log`
--

DROP TABLE IF EXISTS `django_admin_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_admin_log` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `action_time` datetime NOT NULL,
  `user_id` int(11) NOT NULL,
  `content_type_id` int(11) DEFAULT NULL,
  `object_id` longtext,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint(5) unsigned NOT NULL,
  `change_message` longtext NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_user_id_idx` (`user_id`),
  KEY `django_admin_log_content_type_idx` (`content_type_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `django_content_type`
--

DROP TABLE IF EXISTS `django_content_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_content_type` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `app_label` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=39 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `django_session`
--

DROP TABLE IF EXISTS `django_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime NOT NULL,
  PRIMARY KEY (`session_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `django_site`
--

DROP TABLE IF EXISTS `django_site`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_site` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `domain` varchar(100) NOT NULL,
  `name` varchar(50) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
insert into django_site(id,domain,name) values(1,'developer.mozilla.org','developer.mozilla.org');

--
-- Table structure for table `feeder_bundle`
--

DROP TABLE IF EXISTS `feeder_bundle`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `feeder_bundle` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `shortname` varchar(50) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `shortname` (`shortname`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `feeder_bundle_feeds`
--

DROP TABLE IF EXISTS `feeder_bundle_feeds`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `feeder_bundle_feeds` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `bundle_id` int(11) NOT NULL,
  `feed_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `bundle_id` (`bundle_id`,`feed_id`),
  KEY `feed_id_refs_id_55f1514b` (`feed_id`),
  CONSTRAINT `bundle_id_refs_id_1a46350d` FOREIGN KEY (`bundle_id`) REFERENCES `feeder_bundle` (`id`),
  CONSTRAINT `feed_id_refs_id_55f1514b` FOREIGN KEY (`feed_id`) REFERENCES `feeder_feed` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=21 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `feeder_entry`
--

DROP TABLE IF EXISTS `feeder_entry`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `feeder_entry` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `feed_id` int(11) NOT NULL,
  `guid` varchar(255) NOT NULL,
  `raw` longtext NOT NULL,
  `visible` tinyint(1) NOT NULL,
  `last_published` datetime NOT NULL,
  `created` datetime NOT NULL,
  `updated` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `feed_id` (`feed_id`,`guid`),
  KEY `feeder_entry_idx` (`feed_id`),
  CONSTRAINT `feed_id_refs_id_3323b4e` FOREIGN KEY (`feed_id`) REFERENCES `feeder_feed` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `feeder_feed`
--

DROP TABLE IF EXISTS `feeder_feed`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `feeder_feed` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `shortname` varchar(50) NOT NULL,
  `title` varchar(140) NOT NULL,
  `url` varchar(2048) NOT NULL,
  `etag` varchar(140) NOT NULL,
  `last_modified` datetime NOT NULL,
  `enabled` tinyint(1) NOT NULL,
  `disabled_reason` varchar(2048) NOT NULL,
  `keep` int(10) unsigned NOT NULL,
  `created` datetime NOT NULL,
  `updated` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `shortname` (`shortname`)
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `gallery_image`
--

DROP TABLE IF EXISTS `gallery_image`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `gallery_image` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `title` varchar(255) NOT NULL,
  `created` datetime NOT NULL,
  `updated` datetime NOT NULL,
  `updated_by_id` int(11) DEFAULT NULL,
  `description` longtext NOT NULL,
  `locale` varchar(7) NOT NULL,
  `creator_id` int(11) NOT NULL,
  `file` varchar(250) NOT NULL,
  `thumbnail` varchar(250) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `locale` (`locale`,`title`),
  KEY `gallery_image_841a7e28` (`title`),
  KEY `gallery_image_3216ff68` (`created`),
  KEY `gallery_image_8aac229` (`updated`),
  KEY `gallery_image_f90bfc3f` (`updated_by_id`),
  KEY `gallery_image_928541cb` (`locale`),
  KEY `gallery_image_f97a5119` (`creator_id`),
  CONSTRAINT `creator_id_refs_id_9add8201` FOREIGN KEY (`creator_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `updated_by_id_refs_id_9add8201` FOREIGN KEY (`updated_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `gallery_video`
--

DROP TABLE IF EXISTS `gallery_video`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `gallery_video` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `title` varchar(255) NOT NULL,
  `created` datetime NOT NULL,
  `updated` datetime NOT NULL,
  `updated_by_id` int(11) DEFAULT NULL,
  `description` longtext NOT NULL,
  `locale` varchar(7) NOT NULL,
  `creator_id` int(11) NOT NULL,
  `webm` varchar(250) DEFAULT NULL,
  `ogv` varchar(250) DEFAULT NULL,
  `flv` varchar(250) DEFAULT NULL,
  `poster` varchar(250) DEFAULT NULL,
  `thumbnail` varchar(250) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `locale` (`locale`,`title`),
  KEY `gallery_video_841a7e28` (`title`),
  KEY `gallery_video_3216ff68` (`created`),
  KEY `gallery_video_8aac229` (`updated`),
  KEY `gallery_video_f90bfc3f` (`updated_by_id`),
  KEY `gallery_video_928541cb` (`locale`),
  KEY `gallery_video_f97a5119` (`creator_id`),
  CONSTRAINT `creator_id_refs_id_7d7f5ce1` FOREIGN KEY (`creator_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `updated_by_id_refs_id_7d7f5ce1` FOREIGN KEY (`updated_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `notifications_eventwatch`
--

DROP TABLE IF EXISTS `notifications_eventwatch`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `notifications_eventwatch` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `content_type_id` int(11) NOT NULL,
  `watch_id` int(11) DEFAULT NULL,
  `event_type` varchar(20) NOT NULL,
  `locale` varchar(7) NOT NULL,
  `email` varchar(75) NOT NULL,
  `hash` varchar(40) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `content_type_id` (`content_type_id`,`watch_id`,`email`,`event_type`,`locale`),
  KEY `notifications_eventwatch_e4470c6e` (`content_type_id`),
  KEY `notifications_eventwatch_6e1bd094` (`watch_id`),
  KEY `notifications_eventwatch_2be07fce` (`event_type`),
  KEY `notifications_eventwatch_928541cb` (`locale`),
  KEY `notifications_eventwatch_3904588a` (`email`),
  KEY `notifications_eventwatch_36af87d1` (`hash`),
  CONSTRAINT `content_type_id_refs_id_e49edd32` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `notifications_watch`
--

DROP TABLE IF EXISTS `notifications_watch`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `notifications_watch` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `event_type` varchar(30) NOT NULL,
  `content_type_id` int(11) DEFAULT NULL,
  `object_id` int(10) unsigned DEFAULT NULL,
  `user_id` int(11) DEFAULT NULL,
  `email` varchar(75) DEFAULT NULL,
  `secret` varchar(10) DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `notifications_watch_2be07fce` (`event_type`),
  KEY `notifications_watch_e4470c6e` (`content_type_id`),
  KEY `notifications_watch_829e37fd` (`object_id`),
  KEY `notifications_watch_fbfc09f1` (`user_id`),
  KEY `notifications_watch_3904588a` (`email`),
  KEY `notifications_watch_e01be369` (`is_active`),
  CONSTRAINT `content_type_id_refs_id_23da5933` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `user_id_refs_id_2dc6eef1` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `notifications_watchfilter`
--

DROP TABLE IF EXISTS `notifications_watchfilter`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `notifications_watchfilter` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `watch_id` int(11) NOT NULL,
  `name` varchar(20) NOT NULL,
  `value` int(10) unsigned NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`,`watch_id`),
  KEY `notifications_watchfilter_6e1bd094` (`watch_id`),
  CONSTRAINT `watch_id_refs_id_444d6e79` FOREIGN KEY (`watch_id`) REFERENCES `notifications_watch` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `schema_version`
--

DROP TABLE IF EXISTS `schema_version`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `schema_version` (
  `version` int(11) NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tagging_tag`
--

DROP TABLE IF EXISTS `tagging_tag`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tagging_tag` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tagging_taggeditem`
--

DROP TABLE IF EXISTS `tagging_taggeditem`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tagging_taggeditem` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `tag_id` int(11) NOT NULL,
  `content_type_id` int(11) NOT NULL,
  `object_id` int(10) unsigned NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `tag_id` (`tag_id`,`content_type_id`,`object_id`),
  KEY `tagging_taggeditem_3747b463` (`tag_id`),
  KEY `tagging_taggeditem_e4470c6e` (`content_type_id`),
  KEY `tagging_taggeditem_829e37fd` (`object_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `taggit_tag`
--

DROP TABLE IF EXISTS `taggit_tag`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `taggit_tag` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `slug` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `slug` (`slug`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `taggit_taggeditem`
--

DROP TABLE IF EXISTS `taggit_taggeditem`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `taggit_taggeditem` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `tag_id` int(11) NOT NULL,
  `object_id` int(11) NOT NULL,
  `content_type_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `taggit_taggeditem_3747b463` (`tag_id`),
  KEY `taggit_taggeditem_e4470c6e` (`content_type_id`),
  CONSTRAINT `content_type_id_refs_id_5a2b7711` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `tag_id_refs_id_c87e3f85` FOREIGN KEY (`tag_id`) REFERENCES `taggit_tag` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `threadedcomments_freethreadedcomment`
--

DROP TABLE IF EXISTS `threadedcomments_freethreadedcomment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `threadedcomments_freethreadedcomment` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `content_type_id` int(11) NOT NULL,
  `object_id` int(10) unsigned NOT NULL,
  `parent_id` int(11) DEFAULT NULL,
  `name` varchar(128) NOT NULL,
  `website` varchar(200) NOT NULL,
  `email` varchar(75) NOT NULL,
  `date_submitted` datetime NOT NULL,
  `date_modified` datetime NOT NULL,
  `date_approved` datetime DEFAULT NULL,
  `comment` longtext NOT NULL,
  `markup` int(11) DEFAULT NULL,
  `is_public` tinyint(1) NOT NULL,
  `is_approved` tinyint(1) NOT NULL,
  `ip_address` char(15) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `content_type_id_refs_id_b49ecca0` (`content_type_id`),
  KEY `parent_id_refs_id_8c7f0b95` (`parent_id`),
  CONSTRAINT `content_type_id_refs_id_b49ecca0` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `parent_id_refs_id_8c7f0b95` FOREIGN KEY (`parent_id`) REFERENCES `threadedcomments_freethreadedcomment` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `threadedcomments_testmodel`
--

DROP TABLE IF EXISTS `threadedcomments_testmodel`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `threadedcomments_testmodel` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(5) NOT NULL,
  `is_public` tinyint(1) NOT NULL,
  `date` datetime NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `threadedcomments_threadedcomment`
--

DROP TABLE IF EXISTS `threadedcomments_threadedcomment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `threadedcomments_threadedcomment` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `content_type_id` int(11) NOT NULL,
  `object_id` int(10) unsigned NOT NULL,
  `parent_id` int(11) DEFAULT NULL,
  `user_id` int(11) NOT NULL,
  `date_submitted` datetime NOT NULL,
  `date_modified` datetime NOT NULL,
  `date_approved` datetime DEFAULT NULL,
  `comment` longtext NOT NULL,
  `markup` int(11) DEFAULT NULL,
  `is_public` tinyint(1) NOT NULL,
  `is_approved` tinyint(1) NOT NULL,
  `ip_address` char(15) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `content_type_id_refs_id_af49ca3a` (`content_type_id`),
  KEY `user_id_refs_id_3c567b6` (`user_id`),
  KEY `parent_id_refs_id_7ef2a789` (`parent_id`),
  CONSTRAINT `content_type_id_refs_id_af49ca3a` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `parent_id_refs_id_7ef2a789` FOREIGN KEY (`parent_id`) REFERENCES `threadedcomments_threadedcomment` (`id`),
  CONSTRAINT `user_id_refs_id_3c567b6` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `user_profiles`
--

DROP TABLE IF EXISTS `user_profiles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `user_profiles` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `deki_user_id` int(10) unsigned NOT NULL,
  `homepage` varchar(255) NOT NULL,
  `location` varchar(255) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id_refs_id` (`user_id`)
) ENGINE=MyISAM AUTO_INCREMENT=4 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `users_emailchange`
--

DROP TABLE IF EXISTS `users_emailchange`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `users_emailchange` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `activation_key` varchar(40) NOT NULL,
  `email` varchar(75) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  KEY `users_emailchange_3904588a` (`email`),
  CONSTRAINT `user_id_refs_id_7c0fddb0` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `users_profile`
--

DROP TABLE IF EXISTS `users_profile`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `users_profile` (
  `user_id` int(11) NOT NULL,
  `name` varchar(255) DEFAULT NULL,
  `public_email` tinyint(1) NOT NULL,
  `avatar` varchar(250) DEFAULT NULL,
  `bio` longtext,
  `website` varchar(255) DEFAULT NULL,
  `twitter` varchar(255) DEFAULT NULL,
  `facebook` varchar(255) DEFAULT NULL,
  `irc_handle` varchar(255) DEFAULT NULL,
  `timezone` varchar(100) DEFAULT NULL,
  `country` varchar(2) DEFAULT NULL,
  `city` varchar(255) DEFAULT NULL,
  `livechat_id` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`user_id`),
  CONSTRAINT `user_id_refs_id_21617f27` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `users_registrationprofile`
--

DROP TABLE IF EXISTS `users_registrationprofile`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `users_registrationprofile` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `activation_key` varchar(40) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  CONSTRAINT `user_id_refs_id_e9e30776` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `wiki_document`
--

DROP TABLE IF EXISTS `wiki_document`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `wiki_document` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `title` varchar(255) NOT NULL,
  `slug` varchar(255) NOT NULL,
  `is_template` tinyint(1) NOT NULL,
  `is_localizable` tinyint(1) NOT NULL,
  `locale` varchar(7) NOT NULL,
  `current_revision_id` int(11) DEFAULT NULL,
  `parent_id` int(11) DEFAULT NULL,
  `html` longtext NOT NULL,
  `category` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `title` (`title`,`locale`),
  UNIQUE KEY `slug` (`slug`,`locale`),
  UNIQUE KEY `parent_id` (`parent_id`,`locale`),
  KEY `wiki_document_841a7e28` (`title`),
  KEY `wiki_document_a951d5d6` (`slug`),
  KEY `wiki_document_ffc55767` (`is_template`),
  KEY `wiki_document_e8d1d6e4` (`is_localizable`),
  KEY `wiki_document_928541cb` (`locale`),
  KEY `wiki_document_a253e251` (`current_revision_id`),
  KEY `wiki_document_63f17a16` (`parent_id`),
  KEY `wiki_document_34876983` (`category`),
  CONSTRAINT `current_revision_id_refs_id_79f9a479` FOREIGN KEY (`current_revision_id`) REFERENCES `wiki_revision` (`id`),
  CONSTRAINT `parent_id_refs_id_6c4b5a5` FOREIGN KEY (`parent_id`) REFERENCES `wiki_document` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `wiki_firefoxversion`
--

DROP TABLE IF EXISTS `wiki_firefoxversion`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `wiki_firefoxversion` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `item_id` int(11) NOT NULL,
  `document_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `item_id` (`item_id`,`document_id`),
  KEY `wiki_firefoxversion_f4226d13` (`document_id`),
  CONSTRAINT `document_id_refs_id_5d21595b` FOREIGN KEY (`document_id`) REFERENCES `wiki_document` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `wiki_helpfulvote`
--

DROP TABLE IF EXISTS `wiki_helpfulvote`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `wiki_helpfulvote` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `document_id` int(11) NOT NULL,
  `helpful` tinyint(1) NOT NULL,
  `created` datetime NOT NULL,
  `creator_id` int(11) DEFAULT NULL,
  `anonymous_id` varchar(40) NOT NULL,
  `user_agent` varchar(1000) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `wiki_helpfulvote_f4226d13` (`document_id`),
  KEY `wiki_helpfulvote_3216ff68` (`created`),
  KEY `wiki_helpfulvote_f97a5119` (`creator_id`),
  KEY `wiki_helpfulvote_2291b592` (`anonymous_id`),
  CONSTRAINT `creator_id_refs_id_b1375de5` FOREIGN KEY (`creator_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `document_id_refs_id_1ab69a8f` FOREIGN KEY (`document_id`) REFERENCES `wiki_document` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `wiki_operatingsystem`
--

DROP TABLE IF EXISTS `wiki_operatingsystem`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `wiki_operatingsystem` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `item_id` int(11) NOT NULL,
  `document_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `item_id` (`item_id`,`document_id`),
  KEY `wiki_operatingsystem_f4226d13` (`document_id`),
  CONSTRAINT `document_id_refs_id_e92dd159` FOREIGN KEY (`document_id`) REFERENCES `wiki_document` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `wiki_relateddocument`
--

DROP TABLE IF EXISTS `wiki_relateddocument`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `wiki_relateddocument` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `document_id` int(11) NOT NULL,
  `related_id` int(11) NOT NULL,
  `in_common` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `wiki_relateddocument_f4226d13` (`document_id`),
  KEY `wiki_relateddocument_cb822826` (`related_id`),
  CONSTRAINT `document_id_refs_id_5206177f` FOREIGN KEY (`document_id`) REFERENCES `wiki_document` (`id`),
  CONSTRAINT `related_id_refs_id_5206177f` FOREIGN KEY (`related_id`) REFERENCES `wiki_document` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `wiki_revision`
--

DROP TABLE IF EXISTS `wiki_revision`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `wiki_revision` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `document_id` int(11) NOT NULL,
  `summary` longtext NOT NULL,
  `content` longtext NOT NULL,
  `keywords` varchar(255) NOT NULL,
  `created` datetime NOT NULL,
  `reviewed` datetime DEFAULT NULL,
  `significance` int(11) DEFAULT NULL,
  `comment` varchar(255) NOT NULL,
  `reviewer_id` int(11) DEFAULT NULL,
  `creator_id` int(11) NOT NULL,
  `is_approved` tinyint(1) NOT NULL,
  `based_on_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `wiki_revision_f4226d13` (`document_id`),
  KEY `wiki_revision_d0f17e2b` (`reviewer_id`),
  KEY `wiki_revision_f97a5119` (`creator_id`),
  KEY `wiki_revision_c1e306d2` (`is_approved`),
  KEY `wiki_revision_ec4f2057` (`based_on_id`),
  CONSTRAINT `based_on_id_refs_id_cf0bcfb3` FOREIGN KEY (`based_on_id`) REFERENCES `wiki_revision` (`id`),
  CONSTRAINT `creator_id_refs_id_4298f2ad` FOREIGN KEY (`creator_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `document_id_refs_id_226de0df` FOREIGN KEY (`document_id`) REFERENCES `wiki_document` (`id`),
  CONSTRAINT `reviewer_id_refs_id_4298f2ad` FOREIGN KEY (`reviewer_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2011-05-19 15:25:53
