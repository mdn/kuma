CREATE TABLE `kbforums_thread` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `title` varchar(255) NOT NULL,
    `document_id` integer NOT NULL,
    `created` datetime NOT NULL,
    `creator_id` integer NOT NULL,
    `last_post_id` integer,
    `replies` integer NOT NULL,
    `is_locked` bool NOT NULL,
    `is_sticky` bool NOT NULL
)
;
ALTER TABLE `kbforums_thread` ADD CONSTRAINT `creator_id_refs_id_3e559805` FOREIGN KEY (`creator_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `kbforums_thread` ADD CONSTRAINT `document_id_refs_id_42b206f` FOREIGN KEY (`document_id`) REFERENCES `wiki_document` (`id`);
CREATE TABLE `kbforums_post` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `thread_id` integer NOT NULL,
    `content` longtext NOT NULL,
    `creator_id` integer NOT NULL,
    `created` datetime NOT NULL,
    `updated` datetime NOT NULL,
    `updated_by_id` integer
)
;
ALTER TABLE `kbforums_post` ADD CONSTRAINT `creator_id_refs_id_4437f68f` FOREIGN KEY (`creator_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `kbforums_post` ADD CONSTRAINT `updated_by_id_refs_id_4437f68f` FOREIGN KEY (`updated_by_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `kbforums_post` ADD CONSTRAINT `thread_id_refs_id_61d80e19` FOREIGN KEY (`thread_id`) REFERENCES `kbforums_thread` (`id`);
ALTER TABLE `kbforums_thread` ADD CONSTRAINT `last_post_id_refs_id_773178a1` FOREIGN KEY (`last_post_id`) REFERENCES `kbforums_post` (`id`);
CREATE INDEX `kbforums_thread_bdd92ed` ON `kbforums_thread` (`document_id`);
CREATE INDEX `kbforums_thread_3216ff68` ON `kbforums_thread` (`created`);
CREATE INDEX `kbforums_thread_685aee7` ON `kbforums_thread` (`creator_id`);
CREATE INDEX `kbforums_thread_11738784` ON `kbforums_thread` (`last_post_id`);
CREATE INDEX `kbforums_thread_714cf0d8` ON `kbforums_thread` (`is_sticky`);
CREATE INDEX `kbforums_post_65912a8a` ON `kbforums_post` (`thread_id`);
CREATE INDEX `kbforums_post_685aee7` ON `kbforums_post` (`creator_id`);
CREATE INDEX `kbforums_post_3216ff68` ON `kbforums_post` (`created`);
CREATE INDEX `kbforums_post_8aac229` ON `kbforums_post` (`updated`);
CREATE INDEX `kbforums_post_6f403c1` ON `kbforums_post` (`updated_by_id`);COMMIT;

INSERT INTO django_content_type (name, app_label, model) VALUES ('KB Forum Thread', 'kbforums', 'thread');
SET @ct = (SELECT LAST_INSERT_ID());
INSERT INTO auth_permission (name, content_type_id, codename) VALUES
    ('Can add KB threads', @ct, 'add_thread'),
    ('Can lock KB threads', @ct, 'lock_thread'),
    ('Can sticky KB threads', @ct, 'sticky_thread'),
    ('Can change KB threads', @ct, 'change_thread'),
    ('Can delete KB threads', @ct, 'delete_thread');

INSERT INTO django_content_type (name, app_label, model) VALUES ('KB Forum Post', 'kbforums', 'post');
SET @ct = (SELECT LAST_INSERT_ID());
INSERT INTO auth_permission (name, content_type_id, codename) VALUES
    ('Can add KB posts', @ct, 'add_post'),
    ('Can change KB posts', @ct, 'change_post'),
    ('Can delete KB posts', @ct, 'delete_post');
