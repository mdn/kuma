-- gallery app, initial tables
CREATE TABLE `gallery_image` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `title` varchar(255) NOT NULL,
  `created` datetime NOT NULL,
  `updated` datetime NOT NULL,
  `updated_by_id` int(11) DEFAULT NULL,
  `description` longtext NOT NULL,
  `locale` varchar(7) NOT NULL,
  `creator_id` int(11) NOT NULL,
  `file` varchar(100) NOT NULL,
  `thumbnail` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `gallery_image_title` (`title`),
  KEY `gallery_image_created` (`created`),
  KEY `gallery_image_updated` (`updated`),
  KEY `gallery_image_updated_by_id` (`updated_by_id`),
  KEY `gallery_image_locale` (`locale`),
  KEY `gallery_image_creator_id` (`creator_id`),
  CONSTRAINT `creator_id_refs_id_9add8201` FOREIGN KEY (`creator_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `updated_by_id_refs_id_9add8201` FOREIGN KEY (`updated_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `gallery_video` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `title` varchar(255) NOT NULL,
  `created` datetime NOT NULL,
  `updated` datetime NOT NULL,
  `updated_by_id` int(11) DEFAULT NULL,
  `description` longtext NOT NULL,
  `locale` varchar(7) NOT NULL,
  `creator_id` int(11) NOT NULL,
  `file` varchar(100) NOT NULL,
  `thumbnail` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `gallery_video_title` (`title`),
  KEY `gallery_video_created` (`created`),
  KEY `gallery_video_updated` (`updated`),
  KEY `gallery_video_updated_by_id` (`updated_by_id`),
  KEY `gallery_video_locale` (`locale`),
  KEY `gallery_video_creator_id` (`creator_id`),
  CONSTRAINT `creator_id_refs_id_7d7f5ce1` FOREIGN KEY (`creator_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `updated_by_id_refs_id_7d7f5ce1` FOREIGN KEY (`updated_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
