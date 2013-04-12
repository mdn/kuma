BEGIN;
CREATE TABLE `tidings_watch` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `event_type` varchar(30) NOT NULL,
    `content_type_id` integer,
    `object_id` integer UNSIGNED,
    `user_id` integer,
    `email` varchar(75),
    `secret` varchar(10),
    `is_active` bool NOT NULL
)
;
ALTER TABLE `tidings_watch` ADD CONSTRAINT `user_id_refs_id_30bde183` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `tidings_watch` ADD CONSTRAINT `content_type_id_refs_id_6f234cb9` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`);
CREATE TABLE `tidings_watchfilter` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `watch_id` integer NOT NULL,
    `name` varchar(20) NOT NULL,
    `value` integer UNSIGNED NOT NULL,
    UNIQUE (`name`, `watch_id`)
)
;
ALTER TABLE `tidings_watchfilter` ADD CONSTRAINT `watch_id_refs_id_24f0b663` FOREIGN KEY (`watch_id`) REFERENCES `tidings_watch` (`id`);
COMMIT;
