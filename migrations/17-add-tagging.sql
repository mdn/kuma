-- django-taggit stuff: --

CREATE TABLE `taggit_tag` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `name` varchar(100) NOT NULL UNIQUE,
    `slug` varchar(100) NOT NULL UNIQUE
) ENGINE=InnoDB CHARSET=utf8
;
CREATE TABLE `taggit_taggeditem` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `tag_id` integer NOT NULL,
    `object_id` integer NOT NULL,
    `content_type_id` integer NOT NULL
) ENGINE=InnoDB CHARSET=utf8
;
ALTER TABLE `taggit_taggeditem` ADD CONSTRAINT `tag_id_refs_id_c87e3f85` FOREIGN KEY (`tag_id`) REFERENCES `taggit_tag` (`id`);
ALTER TABLE `taggit_taggeditem` ADD CONSTRAINT `content_type_id_refs_id_5a2b7711` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`);
CREATE INDEX `taggit_taggeditem_3747b463` ON `taggit_taggeditem` (`tag_id`);
CREATE INDEX `taggit_taggeditem_e4470c6e` ON `taggit_taggeditem` (`content_type_id`);

-- Added a unique constraint on taggit_tag.name. This keeps tag names case-insensitively unique, since we use MySQL's default collation for utf8, utf8_general_ci.


insert into auth_permission (name, content_type_id, codename) values ('Can add tags to and remove tags from questions', (select id from django_content_type where app_label='questions' and model='question'), 'tag_question');

INSERT INTO django_content_type (name, app_label, model) VALUES ('Tag', 'taggit', 'tag');
SET @ct = (SELECT LAST_INSERT_ID());
INSERT INTO auth_permission (name, content_type_id, codename) VALUES ('Can add tag', @ct, 'add_tag'),
                                                                     ('Can change tag', @ct, 'change_tag'),
                                                                     ('Can delete tag', @ct, 'delete_tag');

INSERT INTO django_content_type (name, app_label, model) VALUES ('Tagged Item', 'taggit', 'taggeditem');
SET @ct = (SELECT LAST_INSERT_ID());
INSERT INTO auth_permission (name, content_type_id, codename) VALUES ('Can add tagged item', @ct, 'add_taggeditem'),
                                                                     ('Can change tagged item', @ct, 'change_taggeditem'),
                                                                     ('Can delete tagged item', @ct, 'delete_taggeditem');
