CREATE TABLE `notifications_watch` (
  `id` integer NOT NULL AUTO_INCREMENT,
  `event_type` varchar(30) binary NOT NULL,
  `content_type_id` integer DEFAULT NULL,
  `object_id` integer unsigned DEFAULT NULL,
  `user_id` integer DEFAULT NULL,
  `email` varchar(75) DEFAULT NULL,
  `secret` varchar(10) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `notifications_watch_2be07fce` (`event_type`),
  KEY `notifications_watch_e4470c6e` (`content_type_id`),
  KEY `notifications_watch_829e37fd` (`object_id`),
  KEY `notifications_watch_fbfc09f1` (`user_id`),
  KEY `notifications_watch_3904588a` (`email`),
  CONSTRAINT `content_type_id_refs_id_23da5933` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `user_id_refs_id_2dc6eef1` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


CREATE TABLE `notifications_watchfilter` (
  `id` integer NOT NULL AUTO_INCREMENT,
  `watch_id` integer NOT NULL,
  `name` binary(20) NOT NULL,
  `value` integer NOT NULL,
  PRIMARY KEY (`id`),
  KEY `notifications_watchfilter_6e1bd094` (`watch_id`),
  KEY `notifications_watchfilter_52094d6e` (`name`),
  CONSTRAINT `watch_id_refs_id_444d6e79` FOREIGN KEY (`watch_id`) REFERENCES `notifications_watch` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
