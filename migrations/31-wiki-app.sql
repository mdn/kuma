CREATE TABLE `wiki_document` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `title` varchar(255) NOT NULL,
    `locale` varchar(7) NOT NULL,
    `current_revision_id` integer NOT NULL,
    `parent_id` integer,
    `html` longtext NOT NULL,
    `category` integer NOT NULL,
    UNIQUE (`parent_id`, `locale`),
    UNIQUE (`title`, `locale`)
)
;
ALTER TABLE `wiki_document` ADD CONSTRAINT `parent_id_refs_id_6c4b5a5` FOREIGN KEY (`parent_id`) REFERENCES `wiki_document` (`id`);
CREATE TABLE `wiki_revision` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `document_id` integer NOT NULL,
    `summary` longtext NOT NULL,
    `content` longtext NOT NULL,
    `keywords` varchar(255) NOT NULL,
    `created` datetime NOT NULL,
    `reviewed` datetime,
    `significance` integer NOT NULL,
    `comment` varchar(255) NOT NULL,
    `reviewer_id` integer,
    `creator_id` integer NOT NULL,
    `is_approved` bool NOT NULL,
    `based_on_id` integer
)
;
ALTER TABLE `wiki_revision` ADD CONSTRAINT `document_id_refs_id_226de0df` FOREIGN KEY (`document_id`) REFERENCES `wiki_document` (`id`);
ALTER TABLE `wiki_revision` ADD CONSTRAINT `reviewer_id_refs_id_4298f2ad` FOREIGN KEY (`reviewer_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `wiki_revision` ADD CONSTRAINT `creator_id_refs_id_4298f2ad` FOREIGN KEY (`creator_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `wiki_document` ADD CONSTRAINT `current_revision_id_refs_id_79f9a479` FOREIGN KEY (`current_revision_id`) REFERENCES `wiki_revision` (`id`);
ALTER TABLE `wiki_revision` ADD CONSTRAINT `based_on_id_refs_id_cf0bcfb3` FOREIGN KEY (`based_on_id`) REFERENCES `wiki_revision` (`id`);
CREATE INDEX `wiki_document_841a7e28` ON `wiki_document` (`title`);
CREATE INDEX `wiki_document_928541cb` ON `wiki_document` (`locale`);
CREATE INDEX `wiki_document_a253e251` ON `wiki_document` (`current_revision_id`);
CREATE INDEX `wiki_document_63f17a16` ON `wiki_document` (`parent_id`);
CREATE INDEX `wiki_revision_f4226d13` ON `wiki_revision` (`document_id`);
CREATE INDEX `wiki_revision_d0f17e2b` ON `wiki_revision` (`reviewer_id`);
CREATE INDEX `wiki_revision_f97a5119` ON `wiki_revision` (`creator_id`);
CREATE INDEX `wiki_revision_ec4f2057` ON `wiki_revision` (`based_on_id`);
