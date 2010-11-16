-- Permission for deleting media
INSERT INTO django_content_type (name, app_label, model) VALUES
    ('Gallery Video', 'gallery', 'video'),
    ('Gallery Image', 'gallery', 'image');
INSERT INTO auth_permission (name, content_type_id, codename) VALUES
    ('Can add image',
     (SELECT id FROM django_content_type
        WHERE app_label='gallery' AND model='image'),
     'add_image'),
    ('Can change image',
     (SELECT id FROM django_content_type
        WHERE app_label='gallery' AND model='image'),
     'change_image'),
    ('Can delete image',
     (SELECT id FROM django_content_type
        WHERE app_label='gallery' AND model='image'),
     'delete_image'),
    ('Can add video',
     (SELECT id FROM django_content_type
        WHERE app_label='gallery' AND model='video'),
     'add_video'),
    ('Can change video',
     (SELECT id FROM django_content_type
        WHERE app_label='gallery' AND model='video'),
     'change_video'),
    ('Can delete video',
     (SELECT id FROM django_content_type
        WHERE app_label='gallery' AND model='video'),
     'delete_video');
