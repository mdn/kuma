BEGIN;

ALTER TABLE `demos_submission` ADD COLUMN (
    `likes_total` integer NOT NULL,
    `likes_recent` integer NOT NULL,
    `launches_total` integer NOT NULL,
    `launches_recent` integer NOT NULL
);

CREATE INDEX `demos_submission_2078387` ON `demos_submission` (`likes_total`);
CREATE INDEX `demos_submission_6ba6244d` ON `demos_submission` (`likes_recent`);
CREATE INDEX `demos_submission_1dc8f9` ON `demos_submission` (`launches_total`);
CREATE INDEX `demos_submission_3984f161` ON `demos_submission` (`launches_recent`);

DROP TABLE IF EXISTS `actioncounters_actioncounterunique`;
CREATE TABLE `actioncounters_actioncounterunique` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `content_type_id` integer NOT NULL,
    `object_pk` varchar(32) NOT NULL,
    `name` varchar(64) NOT NULL,
    `total` integer DEFAULT 0,
    `ip` varchar(40),
    `session_key` varchar(40),
    `user_agent` varchar(255),
    `user_id` integer,
    `modified` datetime
)
;
ALTER TABLE `actioncounters_actioncounterunique` ADD CONSTRAINT `content_type_id_refs_id_a1fb3291` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`);
ALTER TABLE `actioncounters_actioncounterunique` ADD CONSTRAINT `user_id_refs_id_b752f625` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);

CREATE INDEX `actioncounters_actioncounterunique_e4470c6e` ON `actioncounters_actioncounterunique` (`content_type_id`);
CREATE INDEX `actioncounters_actioncounterunique_52094d6e` ON `actioncounters_actioncounterunique` (`name`);
CREATE INDEX `actioncounters_actioncounterunique_49a8a8f2` ON `actioncounters_actioncounterunique` (`ip`);
CREATE INDEX `actioncounters_actioncounterunique_4cac0564` ON `actioncounters_actioncounterunique` (`session_key`);
CREATE INDEX `actioncounters_actioncounterunique_c8b0e61e` ON `actioncounters_actioncounterunique` (`user_agent`);
CREATE INDEX `actioncounters_actioncounterunique_fbfc09f1` ON `actioncounters_actioncounterunique` (`user_id`);

DROP TABLE IF EXISTS `actioncounters_action`;
DROP TABLE IF EXISTS `actioncounters_actioncounter`;
DROP TABLE IF EXISTS `actioncounters_actionhit`;

COMMIT;
