ALTER TABLE `wiki_document` ADD `is_template` tinyint(1) NOT NULL DEFAULT 0;
CREATE INDEX `wiki_document_is_template` ON `wiki_document` (`is_template`);
