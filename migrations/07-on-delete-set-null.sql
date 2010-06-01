ALTER TABLE `forums_thread` DROP FOREIGN KEY `last_post_id_refs_id_3fa89f33`;
ALTER TABLE `forums_thread` ADD CONSTRAINT `last_post_id_refs_id_3fa89f33` FOREIGN KEY (`last_post_id`) REFERENCES `forums_post` (`id`) ON DELETE SET NULL;
ALTER TABLE `forums_forum` DROP FOREIGN KEY `last_post_id_refs_id_e3773179`;
ALTER TABLE `forums_forum` ADD CONSTRAINT `last_post_id_refs_id_e3773179` FOREIGN KEY (`last_post_id`) REFERENCES `forums_post` (`id`) ON DELETE SET NULL;

