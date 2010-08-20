INSERT INTO django_content_type (name, app_label, model) VALUES ('document', 'wiki', 'document');
SET @ct = (SELECT LAST_INSERT_ID());
INSERT INTO auth_permission (name, content_type_id, codename) VALUES ('Can add document', @ct, 'add_document'),
                                                                     ('Can change document', @ct, 'change_document'),
                                                                     ('Can delete document', @ct, 'delete_document');

INSERT INTO django_content_type (name, app_label, model) VALUES ('revision', 'wiki', 'revision');
SET @ct = (SELECT LAST_INSERT_ID());
INSERT INTO auth_permission (name, content_type_id, codename) VALUES ('Can add revision', @ct, 'add_revision'),
                                                                     ('Can change revision', @ct, 'change_revision'),
                                                                     ('Can delete revision', @ct, 'delete_revision');
