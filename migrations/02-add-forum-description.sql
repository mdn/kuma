BEGIN;
-- Application: forums
-- Model: Forum
ALTER TABLE `forums_forum`
	ADD `description` longtext;
ALTER TABLE `forums_forum`
	ADD `last_post_id` integer;
CREATE INDEX `forums_forum_last_post_id_idx`
	ON `forums_forum` (`last_post_id`);
COMMIT;
