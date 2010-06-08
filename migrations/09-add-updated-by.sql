ALTER TABLE `forums_post` ADD `updated_by_id` integer;
ALTER TABLE `forums_post` ADD CONSTRAINT `post_updated_by_id_refs_id_5c0b8875` FOREIGN KEY (`updated_by_id`) REFERENCES `auth_user` (`id`) ON DELETE SET NULL;
