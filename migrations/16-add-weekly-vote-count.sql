ALTER TABLE `questions_question`
    ADD `num_votes_past_week` integer UNSIGNED DEFAULT 0;
CREATE INDEX `questions_question_num_votes_past_week_idx`
    ON `questions_question` (`num_votes_past_week`);
