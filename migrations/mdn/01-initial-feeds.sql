-- 00 syncdb dump
CREATE TABLE `auth_permission` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `name` varchar(50) NOT NULL,
    `content_type_id` integer NOT NULL,
    `codename` varchar(100) NOT NULL,
    UNIQUE (`content_type_id`, `codename`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
;
CREATE TABLE `auth_group_permissions` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `group_id` integer NOT NULL,
    `permission_id` integer NOT NULL,
    UNIQUE (`group_id`, `permission_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
;
ALTER TABLE `auth_group_permissions` ADD CONSTRAINT `permission_id_refs_id_5886d21f` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`);
CREATE TABLE `auth_group` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `name` varchar(80) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
;
ALTER TABLE `auth_group_permissions` ADD CONSTRAINT `group_id_refs_id_3cea63fe` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`);
CREATE TABLE `auth_user_user_permissions` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `user_id` integer NOT NULL,
    `permission_id` integer NOT NULL,
    UNIQUE (`user_id`, `permission_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
;
ALTER TABLE `auth_user_user_permissions` ADD CONSTRAINT `permission_id_refs_id_67e79cb` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`);
CREATE TABLE `auth_user_groups` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `user_id` integer NOT NULL,
    `group_id` integer NOT NULL,
    UNIQUE (`user_id`, `group_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
;
ALTER TABLE `auth_user_groups` ADD CONSTRAINT `group_id_refs_id_f116770` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`);
CREATE TABLE `auth_user` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `username` varchar(30) NOT NULL UNIQUE,
    `first_name` varchar(30) NOT NULL,
    `last_name` varchar(30) NOT NULL,
    `email` varchar(75) NOT NULL,
    `password` varchar(128) NOT NULL,
    `is_staff` bool NOT NULL,
    `is_active` bool NOT NULL,
    `is_superuser` bool NOT NULL,
    `last_login` datetime NOT NULL,
    `date_joined` datetime NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
;
ALTER TABLE `auth_user_user_permissions` ADD CONSTRAINT `user_id_refs_id_dfbab7d` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `auth_user_groups` ADD CONSTRAINT `user_id_refs_id_7ceef80f` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);
CREATE TABLE `auth_message` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `user_id` integer NOT NULL,
    `message` longtext NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
;
ALTER TABLE `auth_message` ADD CONSTRAINT `user_id_refs_id_650f49a6` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);
-- The following references should be added but depend on non-existent tables:
-- ALTER TABLE `auth_permission` ADD CONSTRAINT `content_type_id_refs_id_728de91f` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`);
CREATE INDEX `auth_permission_content_type_id_idx` ON `auth_permission` (`content_type_id`);
CREATE INDEX `auth_message_user_id_idx` ON `auth_message` (`user_id`);
CREATE TABLE `django_content_type` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `name` varchar(100) NOT NULL,
    `app_label` varchar(100) NOT NULL,
    `model` varchar(100) NOT NULL,
    UNIQUE (`app_label`, `model`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
;
CREATE TABLE `django_session` (
    `session_key` varchar(40) NOT NULL PRIMARY KEY,
    `session_data` longtext NOT NULL,
    `expire_date` datetime NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
;
CREATE TABLE `django_site` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `domain` varchar(100) NOT NULL,
    `name` varchar(50) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
;
insert into django_site (id, domain, name) values (1, 'developer.mozilla.org', 'developer.mozilla.org');
CREATE TABLE `django_admin_log` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `action_time` datetime NOT NULL,
    `user_id` integer NOT NULL,
    `content_type_id` integer,
    `object_id` longtext,
    `object_repr` varchar(200) NOT NULL,
    `action_flag` smallint UNSIGNED NOT NULL,
    `change_message` longtext NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
;
-- The following references should be added but depend on non-existent tables:
-- ALTER TABLE `django_admin_log` ADD CONSTRAINT `content_type_id_refs_id_288599e6` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`);
-- ALTER TABLE `django_admin_log` ADD CONSTRAINT `user_id_refs_id_c8665aa` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);
CREATE INDEX `django_admin_log_user_id_idx` ON `django_admin_log` (`user_id`);
CREATE INDEX `django_admin_log_content_type_idx` ON `django_admin_log` (`content_type_id`);

CREATE TABLE `actioncounters_actioncounterunique` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `content_type_id` integer NOT NULL,
    `object_pk` varchar(32) NOT NULL,
    `name` varchar(64) NOT NULL,
    `total` integer NOT NULL,
    `ip` varchar(40),
    `session_key` varchar(40),
    `user_agent` varchar(255),
    `user_id` integer,
    `modified` datetime NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
;
-- The following references should be added but depend on non-existent tables:
-- ALTER TABLE `actioncounters_actioncounterunique` ADD CONSTRAINT `user_id_refs_id_48ad09db` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);
-- ALTER TABLE `actioncounters_actioncounterunique` ADD CONSTRAINT `content_type_id_refs_id_5e04cd6f` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`);
CREATE INDEX `actioncounters_actioncounterunique_content_type_ididx` ON `actioncounters_actioncounterunique` (`content_type_id`);
CREATE INDEX `actioncounters_actioncounterunique_name_idx` ON `actioncounters_actioncounterunique` (`name`);
CREATE INDEX `actioncounters_actioncounterunique_ip_idx` ON `actioncounters_actioncounterunique` (`ip`);
CREATE INDEX `actioncounters_actioncounterunique_session_key_idx` ON `actioncounters_actioncounterunique` (`session_key`);
CREATE INDEX `actioncounters_actioncounterunique_user_agent_idx` ON `actioncounters_actioncounterunique` (`user_agent`);
CREATE INDEX `actioncounters_actioncounterunique_user_id_idx` ON `actioncounters_actioncounterunique` (`user_id`);

CREATE TABLE `user_profiles` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `deki_user_id` integer UNSIGNED NOT NULL,
    `homepage` varchar(255) NOT NULL,
    `location` varchar(255) NOT NULL,
    `user_id` integer
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
;
-- The following references should be added but depend on non-existent tables:
-- ALTER TABLE `user_profiles` ADD CONSTRAINT `user_id_refs_id_69a818e9` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);
CREATE INDEX `user_profiles_idx` ON `user_profiles` (`user_id`);
CREATE TABLE `feeder_bundle_feeds` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `bundle_id` integer NOT NULL,
    `feed_id` integer NOT NULL,
    UNIQUE (`bundle_id`, `feed_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
;
CREATE TABLE `feeder_bundle` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `shortname` varchar(50) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
;
ALTER TABLE `feeder_bundle_feeds` ADD CONSTRAINT `bundle_id_refs_id_1a46350d` FOREIGN KEY (`bundle_id`) REFERENCES `feeder_bundle` (`id`);
CREATE TABLE `feeder_feed` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `shortname` varchar(50) NOT NULL UNIQUE,
    `title` varchar(140) NOT NULL,
    `url` varchar(2048) NOT NULL,
    `etag` varchar(140) NOT NULL,
    `last_modified` datetime NOT NULL,
    `enabled` bool NOT NULL,
    `disabled_reason` varchar(2048) NOT NULL,
    `keep` integer UNSIGNED NOT NULL,
    `created` datetime NOT NULL,
    `updated` datetime NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
;
ALTER TABLE `feeder_bundle_feeds` ADD CONSTRAINT `feed_id_refs_id_55f1514b` FOREIGN KEY (`feed_id`) REFERENCES `feeder_feed` (`id`);
CREATE TABLE `feeder_entry` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `feed_id` integer NOT NULL,
    `guid` varchar(255) NOT NULL,
    `raw` longtext NOT NULL,
    `visible` bool NOT NULL,
    `last_published` datetime NOT NULL,
    `created` datetime NOT NULL,
    `updated` datetime NOT NULL,
    UNIQUE (`feed_id`, `guid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
;
ALTER TABLE `feeder_entry` ADD CONSTRAINT `feed_id_refs_id_3323b4e` FOREIGN KEY (`feed_id`) REFERENCES `feeder_feed` (`id`);
CREATE INDEX `feeder_entry_idx` ON `feeder_entry` (`feed_id`);
-- end 00

INSERT INTO `feeder_feed` (`id`, `shortname`, `url`, `enabled`, `keep`, `created`, `updated`) VALUES
(1, 'moz-hacks', 'http://hacks.mozilla.org/feed/', 1, 50, NOW(), NOW()),
(2, 'tw-mozhacks', 'http://twitter.com/statuses/user_timeline/45496942.rss', 1, 50, NOW(), NOW()),
(3, 'tw-mozillaweb', 'http://twitter.com/statuses/user_timeline/38209403.rss', 1, 50, NOW(), NOW()),
(4, 'tw-mozmobile', 'http://twitter.com/statuses/user_timeline/67033966.rss', 1, 50, NOW(), NOW()),
(5, 'tw-mozillaqa', 'http://twitter.com/statuses/user_timeline/24752152.rss', 1, 50, NOW(), NOW()),
(6, 'planet-mobile', 'http://planet.firefox.com/mobile/rss20.xml', 1, 50, NOW(), NOW()),
(7, 'tw-mozamo', 'http://twitter.com/statuses/user_timeline/15383463.rss', 1, 50, NOW(), NOW()),
(8, 'tw-planetmozilla', 'http://twitter.com/statuses/user_timeline/39292665.rss', 1, 50, NOW(), NOW())
;
