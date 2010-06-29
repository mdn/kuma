CREATE TABLE `questions_answervote` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `answer_id` integer NOT NULL,
    `helpful` bool NOT NULL,
    `created` datetime NOT NULL,
    `creator_id` integer,
    `anonymous_id` varchar(40) NOT NULL
) ENGINE=InnoDB CHARSET=utf8
;
ALTER TABLE `questions_answervote` ADD CONSTRAINT `answer_id_refs_id_112ad03b` FOREIGN KEY (`answer_id`) REFERENCES `questions_answer` (`id`);
ALTER TABLE `questions_answervote` ADD CONSTRAINT `creator_id_refs_id_73284cb0` FOREIGN KEY (`creator_id`) REFERENCES `auth_user` (`id`);
CREATE INDEX `questions_answervote_answer_id` ON `questions_answervote` (`answer_id`);
CREATE INDEX `questions_answervote_created` ON `questions_answervote` (`created`);
CREATE INDEX `questions_answervote_creator_id` ON `questions_answervote` (`creator_id`);
CREATE INDEX `questions_answervote_anonymous_id` ON `questions_answervote` (`anonymous_id`);
