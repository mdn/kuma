INSERT INTO auth_permission (name, content_type_id, codename)
    VALUES ('Can review a revision',
            (select id from django_content_type where app_label='wiki' and model='revision'),
            'review_revision');
