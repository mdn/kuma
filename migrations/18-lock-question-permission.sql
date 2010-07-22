INSERT INTO auth_permission (name, content_type_id, codename)
    VALUES ('Can lock question',
            (select id from django_content_type where app_label='questions' and model='question'),
            'lock_question');
