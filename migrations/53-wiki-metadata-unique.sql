ALTER TABLE `wiki_firefoxversion`
    DROP INDEX `wiki_firefoxversion_67b70d25`;
ALTER TABLE `wiki_firefoxversion`
    ADD UNIQUE (`item_id`, `document_id`);
ALTER TABLE `wiki_operatingsystem`
    DROP INDEX `wiki_operatingsystem_67b70d25`;
ALTER TABLE `wiki_operatingsystem`
    ADD UNIQUE (`item_id`, `document_id`);
