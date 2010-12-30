CREATE TABLE `users_emailchange` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `user_id` integer NOT NULL UNIQUE,
    `activation_key` varchar(40) NOT NULL,
    `email` varchar(75)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
ALTER TABLE `users_emailchange`
    ADD CONSTRAINT `user_id_refs_id_7c0fddb0` FOREIGN KEY (`user_id`)
        REFERENCES `auth_user` (`id`);
CREATE INDEX `users_emailchange_email`
    ON `users_emailchange` (`email`);
