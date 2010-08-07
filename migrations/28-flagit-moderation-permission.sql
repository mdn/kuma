INSERT INTO django_content_type (name, app_label, model) VALUES ('Flagged Object', 'flagit', 'flaggedobject');
SET @ct = (SELECT LAST_INSERT_ID());
INSERT INTO auth_permission (name, content_type_id, codename) VALUES ('Can moderate flagged objects', @ct, 'can_moderate');
