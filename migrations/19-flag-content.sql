CREATE TABLE `flagit_flaggedobject` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `content_type_id` integer NOT NULL,
    `object_id` integer UNSIGNED NOT NULL,
    `status` integer NOT NULL,
    `reason` varchar(64) NOT NULL,
    `notes` longtext NOT NULL,
    `creator_id` integer NOT NULL,
    `created` datetime NOT NULL,
    `handled` datetime NOT NULL,
    `handled_by_id` integer,
    UNIQUE (`content_type_id`, `object_id`, `creator_id`)
)
;
ALTER TABLE `flagit_flaggedobject` ADD CONSTRAINT `content_type_id_refs_id_6f4cf8f9` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`);
ALTER TABLE `flagit_flaggedobject` ADD CONSTRAINT `creator_id_refs_id_402bce45` FOREIGN KEY (`creator_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `flagit_flaggedobject` ADD CONSTRAINT `handled_by_id_refs_id_402bce45` FOREIGN KEY (`handled_by_id`) REFERENCES `auth_user` (`id`);
CREATE INDEX `flagit_flaggedobject_e4470c6e` ON `flagit_flaggedobject` (`content_type_id`);
CREATE INDEX `flagit_flaggedobject_c9ad71dd` ON `flagit_flaggedobject` (`status`);
CREATE INDEX `flagit_flaggedobject_f97a5119` ON `flagit_flaggedobject` (`creator_id`);
CREATE INDEX `flagit_flaggedobject_3216ff68` ON `flagit_flaggedobject` (`created`);
CREATE INDEX `flagit_flaggedobject_a8d7f3ae` ON `flagit_flaggedobject` (`handled`);
CREATE INDEX `flagit_flaggedobject_c77d7f80` ON `flagit_flaggedobject` (`handled_by_id`);
