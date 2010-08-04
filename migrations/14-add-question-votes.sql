CREATE TABLE `questions_questionvote` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `question_id` integer NOT NULL,
    `created` datetime NOT NULL,
    `creator_id` integer,
    `anonymous_id` varchar(40) NOT NULL
) ENGINE=InnoDB CHARSET=utf8
;
ALTER TABLE `questions_questionvote` ADD CONSTRAINT `question_id_refs_id_9dde00db` FOREIGN KEY (`question_id`) REFERENCES `questions_question` (`id`);
ALTER TABLE `questions_questionvote` ADD CONSTRAINT `creator_id_refs_id_699edd80` FOREIGN KEY (`creator_id`) REFERENCES `auth_user` (`id`);
CREATE INDEX `questions_questionvote_question_id` ON `questions_questionvote` (`question_id`);
CREATE INDEX `questions_questionvote_created` ON `questions_questionvote` (`created`);
CREATE INDEX `questions_questionvote_creator_id` ON `questions_questionvote` (`creator_id`);
CREATE INDEX `questions_questionvote_anonymous_id` ON `questions_questionvote` (`anonymous_id`);

INSERT INTO django_content_type (name, app_label, model) VALUES ('question vote', 'questions', 'questionvote');
SET @ct = (SELECT LAST_INSERT_ID());
INSERT INTO auth_permission (name, content_type_id, codename) VALUES ('Can add question vote', @ct, 'add_questionvote'),
                                                                     ('Can change question vote', @ct, 'change_questionvote'),
                                                                     ('Can delete question vote', @ct, 'delete_questionvote');
