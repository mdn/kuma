-- tables managed via migration instead of syncdb...
DROP TABLE IF EXISTS `user_profiles`;

BEGIN;
CREATE TABLE `user_profiles` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `deki_user_id` integer UNSIGNED NOT NULL,
    `homepage` varchar(255) NOT NULL,
    `location` varchar(255) NOT NULL,
    `user_id` integer
)
;
ALTER TABLE `user_profiles` ADD CONSTRAINT `user_id_refs_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);
COMMIT;
