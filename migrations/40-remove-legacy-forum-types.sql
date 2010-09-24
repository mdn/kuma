-- Remove the content type and permissions for legacy forum models.

SET @ct = (SELECT id FROM django_content_type WHERE app_label = 'sumo' AND model = 'forum');
DELETE FROM auth_permission WHERE content_type_id = @ct;
DELETE FROM django_content_type WHERE id = @ct;

SET @ct = (SELECT id FROM django_content_type WHERE app_label = 'sumo' AND model = 'forumthread');
DELETE FROM auth_permission WHERE content_type_id = @ct;
DELETE FROM django_content_type WHERE id = @ct;
