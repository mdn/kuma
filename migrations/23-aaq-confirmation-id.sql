ALTER TABLE `questions_question` ADD `confirmation_id` varchar(40) NOT NULL;
CREATE INDEX `questions_question_confirmation_id` ON `questions_question` (`confirmation_id`);

UPDATE questions_question SET status = 1;
