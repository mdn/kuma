-- Model: Answer
ALTER TABLE `questions_answer`
    ADD `page` integer default 1;

-- Set page numbers for existing answers.
UPDATE questions_answer a
SET
    page = (
        SELECT COUNT(*)
        FROM (
            SELECT id, question_id, created
            FROM questions_answer) b
        WHERE b.question_id = a.question_id AND b.created < a.created
        ) / 20 + 1;
