--
-- New tables for comments on demo room submissions
-- ./manage.py sql threadedcomments
--

BEGIN;
DROP TABLE IF EXISTS `threadedcomments_threadedcomment`;
CREATE TABLE `threadedcomments_threadedcomment` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `content_type_id` integer NOT NULL,
    `object_id` integer UNSIGNED NOT NULL,
    `parent_id` integer,
    `user_id` integer NOT NULL,
    `date_submitted` datetime NOT NULL,
    `date_modified` datetime NOT NULL,
    `date_approved` datetime,
    `comment` longtext NOT NULL,
    `markup` integer,
    `is_public` bool NOT NULL,
    `is_approved` bool NOT NULL,
    `ip_address` char(15)
)
;
ALTER TABLE `threadedcomments_threadedcomment` ADD CONSTRAINT `content_type_id_refs_id_af49ca3a` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`);
ALTER TABLE `threadedcomments_threadedcomment` ADD CONSTRAINT `user_id_refs_id_3c567b6` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `threadedcomments_threadedcomment` ADD CONSTRAINT `parent_id_refs_id_7ef2a789` FOREIGN KEY (`parent_id`) REFERENCES `threadedcomments_threadedcomment` (`id`);
DROP TABLE IF EXISTS `threadedcomments_freethreadedcomment`;
CREATE TABLE `threadedcomments_freethreadedcomment` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `content_type_id` integer NOT NULL,
    `object_id` integer UNSIGNED NOT NULL,
    `parent_id` integer,
    `name` varchar(128) NOT NULL,
    `website` varchar(200) NOT NULL,
    `email` varchar(75) NOT NULL,
    `date_submitted` datetime NOT NULL,
    `date_modified` datetime NOT NULL,
    `date_approved` datetime,
    `comment` longtext NOT NULL,
    `markup` integer,
    `is_public` bool NOT NULL,
    `is_approved` bool NOT NULL,
    `ip_address` char(15)
)
;
ALTER TABLE `threadedcomments_freethreadedcomment` ADD CONSTRAINT `content_type_id_refs_id_b49ecca0` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`);
ALTER TABLE `threadedcomments_freethreadedcomment` ADD CONSTRAINT `parent_id_refs_id_8c7f0b95` FOREIGN KEY (`parent_id`) REFERENCES `threadedcomments_freethreadedcomment` (`id`);
DROP TABLE IF EXISTS `threadedcomments_testmodel`;
CREATE TABLE `threadedcomments_testmodel` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `name` varchar(5) NOT NULL,
    `is_public` bool NOT NULL,
    `date` datetime NOT NULL
)
;
COMMIT;

