ALTER TABLE `wiki_document` ADD `is_localizable` tinyint(1) NOT NULL DEFAULT 1;
CREATE INDEX `wiki_document_is_localizable` ON `wiki_document` (`is_template`);
