CREATE TABLE `users_registrationprofile` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `user_id` integer NOT NULL UNIQUE,
    `activation_key` varchar(40) NOT NULL
);
ALTER TABLE `users_registrationprofile` ADD CONSTRAINT `user_id_refs_id_e9e30776` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);
