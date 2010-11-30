CREATE TABLE `users_profile` (
  `user_id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
