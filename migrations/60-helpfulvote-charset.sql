-- Fix the charset and engine of wiki_helpfulvote.

ALTER TABLE `wiki_helpfulvote`
    DROP INDEX `wiki_helpfulvote_2291b592`;

ALTER TABLE `wiki_helpfulvote`
    MODIFY COLUMN `anonymous_id` BLOB,
    MODIFY COLUMN `user_agent` BLOB;

ALTER TABLE `wiki_helpfulvote`
    MODIFY COLUMN `anonymous_id` VARCHAR(40) CHARACTER SET utf8 NOT NULL,
    MODIFY COLUMN `user_agent` VARCHAR(1000) CHARACTER SET utf8 NOT NULL;

ALTER TABLE `wiki_helpfulvote`
    CONVERT TO CHARACTER SET utf8 COLLATE utf8_unicode_ci;

ALTER TABLE `wiki_helpfulvote`
    ENGINE=InnoDB;

ALTER TABLE `wiki_helpfulvote`
    ADD INDEX `wiki_helpfulvote_2291b592` ( `anonymous_id` );
