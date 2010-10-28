-- Put the is_localizable index on is_localizable.
ALTER TABLE `wiki_document` DROP INDEX `wiki_document_is_localizable`;
ALTER TABLE `wiki_document` ADD INDEX `wiki_document_is_localizable` ( `is_localizable` );
