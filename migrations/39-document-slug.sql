ALTER TABLE `wiki_document` ADD `slug` varchar(255) NOT NULL;
CREATE INDEX `wiki_document_slug` ON `wiki_document` (`slug`);
CREATE UNIQUE INDEX `slug` ON `wiki_document` (`slug`,`locale`);
