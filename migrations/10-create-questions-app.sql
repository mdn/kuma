BEGIN;
CREATE TABLE `questions_questionforum` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `name` varchar(50) NOT NULL UNIQUE,
    `slug` varchar(50) NOT NULL UNIQUE
) ENGINE=InnoDB CHARSET=utf8
;
CREATE TABLE `questions_question` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `title` varchar(255) NOT NULL,
    `forum_id` integer NOT NULL,
    `creator_id` integer NOT NULL,
    `content` longtext NOT NULL,
    `created` datetime NOT NULL,
    `updated` datetime,
    `updated_by_id` integer,
    `last_answer_id` integer,
    `num_answers` integer NOT NULL,
    `status` integer NOT NULL,
    `is_locked` bool NOT NULL
) ENGINE=InnoDB CHARSET=utf8
;
ALTER TABLE `questions_question` ADD CONSTRAINT `creator_id_refs_id_723e3a28` FOREIGN KEY (`creator_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `questions_question` ADD CONSTRAINT `updated_by_id_refs_id_723e3a28` FOREIGN KEY (`updated_by_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `questions_question` ADD CONSTRAINT `forum_id_refs_id_334b13f3` FOREIGN KEY (`forum_id`) REFERENCES `questions_questionforum` (`id`);
CREATE TABLE `questions_questionmetadata` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `question_id` integer NOT NULL,
    `name` varchar(50) NOT NULL,
    `value` longtext NOT NULL
) ENGINE=InnoDB CHARSET=utf8
;
ALTER TABLE `questions_questionmetadata` ADD CONSTRAINT `question_id_refs_id_199b1870` FOREIGN KEY (`question_id`) REFERENCES `questions_question` (`id`);
CREATE TABLE `questions_answer` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `question_id` integer NOT NULL,
    `creator_id` integer NOT NULL,
    `created` datetime NOT NULL,
    `content` longtext NOT NULL,
    `updated` datetime,
    `updated_by_id` integer,
    `upvotes` integer NOT NULL
) ENGINE=InnoDB CHARSET=utf8
;
ALTER TABLE `questions_answer` ADD CONSTRAINT `creator_id_refs_id_30a2e948` FOREIGN KEY (`creator_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `questions_answer` ADD CONSTRAINT `updated_by_id_refs_id_30a2e948` FOREIGN KEY (`updated_by_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `questions_answer` ADD CONSTRAINT `question_id_refs_id_5dadc1b3` FOREIGN KEY (`question_id`) REFERENCES `questions_question` (`id`);
ALTER TABLE `questions_question` ADD CONSTRAINT `last_answer_id_refs_id_6a0465b3` FOREIGN KEY (`last_answer_id`) REFERENCES `questions_answer` (`id`);
CREATE INDEX `questions_question_forum_id` ON `questions_question` (`forum_id`);
CREATE INDEX `questions_question_creator_id` ON `questions_question` (`creator_id`);
CREATE INDEX `questions_question_created` ON `questions_question` (`created`);
CREATE INDEX `questions_question_updated` ON `questions_question` (`updated`);
CREATE INDEX `questions_question_updated_by_id` ON `questions_question` (`updated_by_id`);
CREATE INDEX `questions_question_last_answer_id` ON `questions_question` (`last_answer_id`);
CREATE INDEX `questions_question_num_answers` ON `questions_question` (`num_answers`);
CREATE INDEX `questions_question_status` ON `questions_question` (`status`);
CREATE INDEX `questions_questionmetadata_question_id` ON `questions_questionmetadata` (`question_id`);
CREATE INDEX `questions_questionmetadata_name` ON `questions_questionmetadata` (`name`);
CREATE INDEX `questions_answer_question_id` ON `questions_answer` (`question_id`);
CREATE INDEX `questions_answer_creator_id` ON `questions_answer` (`creator_id`);
CREATE INDEX `questions_answer_created` ON `questions_answer` (`created`);
CREATE INDEX `questions_answer_updated` ON `questions_answer` (`updated`);
CREATE INDEX `questions_answer_updated_by_id` ON `questions_answer` (`updated_by_id`);
CREATE INDEX `questions_answer_upvotes` ON `questions_answer` (`upvotes`);
COMMIT;
