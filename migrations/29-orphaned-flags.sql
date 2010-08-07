-- Delete orphaned flags on questions
DELETE FROM
    flagit_flaggedobject
WHERE
    object_id NOT IN
        (
        SELECT
            q.id
        FROM
            questions_question q
        )
    AND content_type_id =
        (
        SELECT
            id
        FROM
            django_content_type
        WHERE
            name = 'question'
            AND app_label = 'questions'
        );


-- Delete orphaned flags on answers
DELETE FROM
    flagit_flaggedobject
WHERE
    object_id NOT IN
        (
        SELECT
            a.id
        FROM
            questions_answer a
        )
    AND content_type_id =
        (
        SELECT
            id
        FROM
            django_content_type
        WHERE
            name = 'answer'
            AND app_label = 'questions'
        );
