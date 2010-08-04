CREATE UNIQUE INDEX `questions_questionmetadata_question_and_name_idx`
    ON `questions_questionmetadata` (`question_id`, `name`);
