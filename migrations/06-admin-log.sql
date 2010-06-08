CREATE TABLE IF NOT EXISTS `django_admin_log` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `action_time` datetime NOT NULL,
    `user_id` integer NOT NULL,
    `content_type_id` integer,
    `object_id` longtext,
    `object_repr` varchar(200) NOT NULL,
    `action_flag` smallint UNSIGNED NOT NULL,
    `change_message` longtext NOT NULL
) ENGINE=InnoDB CHARACTER SET utf8 COLLATE utf8_general_ci
;
ALTER TABLE `django_admin_log` ADD CONSTRAINT `content_type_id_refs_id_288599e6` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`);
ALTER TABLE `django_admin_log` ADD CONSTRAINT `user_id_refs_id_c8665aa` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);
CREATE INDEX `django_admin_log_user_id` ON `django_admin_log` (`user_id`);
CREATE INDEX `django_admin_log_content_type_id` ON `django_admin_log` (`content_type_id`);
COMMIT;
