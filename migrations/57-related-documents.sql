-- Create RelatedDocument table and some helpful indexes.

CREATE TABLE `wiki_relateddocument` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `document_id` integer NOT NULL,
    `related_id` integer NOT NULL,
    `in_common` integer NOT NULL
) ENGINE=InnoDB CHARACTER SET utf8 COLLATE utf8_general_ci;

ALTER TABLE `wiki_relateddocument` ADD CONSTRAINT `document_id_refs_id_5206177f` FOREIGN KEY (`document_id`) REFERENCES `wiki_document` (`id`);
ALTER TABLE `wiki_relateddocument` ADD CONSTRAINT `related_id_refs_id_5206177f` FOREIGN KEY (`related_id`) REFERENCES `wiki_document` (`id`);
CREATE INDEX `wiki_document_34876983` ON `wiki_document` (`category`);
