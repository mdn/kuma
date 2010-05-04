BEGIN;
-- Application: forums
-- Model: Forum
ALTER TABLE `forums_forum`
	MODIFY `id` integer AUTO_INCREMENT;
ALTER TABLE `forums_forum`
	MODIFY `name` varchar(50);
ALTER TABLE `forums_forum`
	MODIFY `slug` varchar(50);
-- Model: Thread
ALTER TABLE `forums_thread`
	ADD `is_sticky` bool;
CREATE INDEX `forums_thread_is_sticky_idx`
	ON `forums_thread` (`is_sticky`);
ALTER TABLE `forums_thread`
	MODIFY `is_locked` bool;
ALTER TABLE `forums_thread`
	MODIFY `id` integer AUTO_INCREMENT;
ALTER TABLE `forums_thread`
	MODIFY `title` varchar(255);
-- Model: Post
ALTER TABLE `forums_post`
	MODIFY `id` integer AUTO_INCREMENT;
COMMIT;
