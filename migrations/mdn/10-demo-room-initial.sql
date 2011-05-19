--
-- Initial tables and data for Demo Gallery
--

--
-- Table structure for table `actioncounters_actionhit`
--

DROP TABLE IF EXISTS `actioncounters_actionhit`;
CREATE TABLE `actioncounters_actionhit` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `counter_id` int(11) NOT NULL,
  `total` int(11) NOT NULL,
  `ip` varchar(40) DEFAULT NULL,
  `session_key` varchar(40) DEFAULT NULL,
  `user_agent` varchar(255) DEFAULT NULL,
  `user_id` int(11) DEFAULT NULL,
  `created` datetime NOT NULL,
  PRIMARY KEY (`id`),
-- TODO re-enable  UNIQUE KEY `ip` (`ip`,`session_key`,`user_agent`,`user_id`),
  KEY `actioncounters_actionhit_7952d08b` (`counter_id`),
  KEY `actioncounters_actionhit_fbfc09f1` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Table structure for table `contentflagging_contentflag`
--

DROP TABLE IF EXISTS `contentflagging_contentflag`;
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
-- TODO re-enable  UNIQUE KEY `content_type_id` (`content_type_id`,`object_pk`,`ip`,`session_key`,`user_agent`,`user_id`),
  KEY `contentflagging_contentflag_68c2f437` (`flag_type`),
  KEY `contentflagging_contentflag_e4470c6e` (`content_type_id`),
  KEY `contentflagging_contentflag_fbfc09f1` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Table structure for table `demos_submission`
--

DROP TABLE IF EXISTS `demos_submission`;
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
  PRIMARY KEY (`id`),
  UNIQUE KEY `title` (`title`),
  UNIQUE KEY `slug` (`slug`),
  KEY `demos_submission_f97a5119` (`creator_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Table structure for table `demos_tagdescription`
--

DROP TABLE IF EXISTS `demos_tagdescription`;
CREATE TABLE `demos_tagdescription` (
  `tag_name` varchar(50) NOT NULL,
  `title` varchar(255) NOT NULL,
  `description` longtext NOT NULL,
  PRIMARY KEY (`tag_name`),
  UNIQUE KEY `title` (`title`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Dumping data for table `demos_tagdescription`
--

INSERT INTO `demos_tagdescription` VALUES 
('audio','Audio','These demos make noise'),
('canvas','Canvas','These demos make pretty pictures'),
('css3','CSS3','Fancy styling happens in these demos'),
('device','Device','Demos here use device thingies'),
('file','File','Files are manipulated here'),
('game','Game','Games are demos too!'),
('geolocation','Geolocation','These demos know where you\'ve been'),
('html5','HTML5','HTML5 is the future!'),
('indexeddb','IndexedDB','Data gets indexed happily'),
('mobile','Mobile','Demos on the march!'),
('svg','SVG','Drawrings in demos vectorly'),
('video','Video','Internet killed the video star'),
('webgl','WebGL','The browser is throwing things at your face in 3D'),
('websockets','WebSockets','Stick these in your socket and network it'),
('forms','Forms','Filling out fields just got better'),
('mathml','MathML','Pretty math stuff'),
('smil','SMIL','SMILe, you\'re on candid web demos'),
('localstorage','Local Storage','Storing things locally'),
('offlinesupport','Offline Support','Going offline for awhile'),
('webworkers','Web Workers','Workers of the web unite!');

--
-- Table structure for table `tagging_taggeditem`
--

DROP TABLE IF EXISTS `tagging_taggeditem`;
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

--
-- Table structure for table `tagging_tag`
--

DROP TABLE IF EXISTS `tagging_tag`;
CREATE TABLE `tagging_tag` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
