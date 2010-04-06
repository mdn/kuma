CREATE TABLE IF NOT EXISTS `tiki_freetags` (
  `tagId` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `tag` varchar(30) NOT NULL DEFAULT '',
  `raw_tag` varchar(50) NOT NULL DEFAULT '',
  `lang` varchar(16) DEFAULT NULL,
  PRIMARY KEY (`tagId`)
) ENGINE=MyISAM AUTO_INCREMENT=12176 DEFAULT CHARSET=latin1;

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

INSERT INTO tiki_objects (objectId, type, itemId, name) VALUES (79, 'wiki page', 'Firefox Support Home Page', 'Firefox Support Home Page');
INSERT INTO tiki_objects (objectId, type, itemId, name) VALUES (84, 'wiki page', 'Style Guide', 'Style Guide');
INSERT INTO tiki_objects (objectId, type, itemId, name) VALUES (62, 'wiki page', 'Video or audio does not play', 'Video or audio does not play');

CREATE TABLE IF NOT EXISTS `tiki_category_objects` (
  `catObjectId` int(12) NOT NULL DEFAULT '0',
  `categId` int(12) NOT NULL DEFAULT '0',
  PRIMARY KEY (`catObjectId`,`categId`),
  KEY `categId` (`categId`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

INSERT INTO tiki_category_objects (catObjectId, categId) VALUES (79, 8), (84, 23), (62, 1), (62, 13), (62, 14), (62, 19), (62, 25);
