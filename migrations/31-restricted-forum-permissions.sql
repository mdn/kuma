SET @ct = (SELECT id FROM django_content_type WHERE app_label='forums' AND model='forum');
INSERT INTO auth_permission (name, content_type_id, codename) VALUES
    ('Can view restricted forums', @ct, 'view_in_forum'),
    ('Can post in restricted forums', @ct, 'post_in_forum');
